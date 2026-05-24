#include <chrono>
#include <cmath>
#include <limits>
#include <optional>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

// Publishes a ping on /benchmark at a fixed interval, records the send time,
// and computes one-way latency when an /ack arrives.
// The payload embeds the send timestamp (nanoseconds) so the remote side can
// echo it back for a fully-paired RTT measurement if desired.
class TopicLatencyBenchmarkNode : public rclcpp::Node
{
public:
  TopicLatencyBenchmarkNode()
  : Node("topic_latency_benchmark")
  {
    benchmark_topic_   = this->declare_parameter<std::string>("benchmark_topic", "/benchmark");
    ack_topic_         = this->declare_parameter<std::string>("ack_topic", "/ack");
    publish_interval_ms_ = this->declare_parameter<int>("publish_interval_ms", 100);

    auto qos = rclcpp::QoS(rclcpp::KeepLast(10));

    benchmark_pub_ = this->create_publisher<std_msgs::msg::String>(benchmark_topic_, qos);

    ack_sub_ = this->create_subscription<std_msgs::msg::String>(
      ack_topic_,
      qos,
      std::bind(&TopicLatencyBenchmarkNode::onAck, this, std::placeholders::_1));

    publish_timer_ = this->create_wall_timer(
      std::chrono::milliseconds(publish_interval_ms_),
      std::bind(&TopicLatencyBenchmarkNode::publishBenchmark, this));

    stats_timer_ = this->create_wall_timer(
      std::chrono::seconds(5),
      std::bind(&TopicLatencyBenchmarkNode::printStats, this));

    RCLCPP_INFO(
      this->get_logger(),
      "Benchmark node started. Publishing to '%s', listening on '%s'. Interval: %d ms.",
      benchmark_topic_.c_str(), ack_topic_.c_str(), publish_interval_ms_);
  }

private:
  void publishBenchmark()
  {
    last_publish_time_ = clock_.now();

    auto msg = std_msgs::msg::String();
    // Embed nanosecond timestamp so a remote echo node can return it for true RTT.
    msg.data = std::to_string(last_publish_time_->nanoseconds());
    benchmark_pub_->publish(msg);

    RCLCPP_INFO(
      this->get_logger(),
      "/benchmark published at %.9f s  (seq %zu)",
      last_publish_time_->seconds(), ++seq_);
  }

  void onAck(const std_msgs::msg::String::SharedPtr msg)
  {
    const auto rx_time = clock_.now();

    RCLCPP_INFO(
      this->get_logger(),
      "/ack received at %.9f s  payload='%s'",
      rx_time.seconds(), msg->data.c_str());

    if (!last_publish_time_.has_value()) {
      RCLCPP_WARN(this->get_logger(), "/ack before any /benchmark publish; skipping.");
      return;
    }

    const double latency_ms = (rx_time - *last_publish_time_).seconds() * 1000.0;

    if (latency_ms < 0.0) {
      RCLCPP_WARN(this->get_logger(), "Negative latency (%.3f ms); skipping.", latency_ms);
      return;
    }

    count_++;
    sum_ms_ += latency_ms;
    min_ms_ = std::min(min_ms_, latency_ms);
    max_ms_ = std::max(max_ms_, latency_ms);

    RCLCPP_INFO(
      this->get_logger(),
      "Latency /benchmark → /ack: %.3f ms  (sample %zu)",
      latency_ms, count_);
  }

  void printStats()
  {
    if (count_ == 0) {
      RCLCPP_INFO(this->get_logger(), "No paired samples yet.");
      return;
    }

    const double avg_ms = sum_ms_ / static_cast<double>(count_);
    RCLCPP_INFO(
      this->get_logger(),
      "Stats over %zu samples: min=%.3f ms  avg=%.3f ms  max=%.3f ms",
      count_, min_ms_, avg_ms, max_ms_);
  }

  std::string benchmark_topic_;
  std::string ack_topic_;
  int publish_interval_ms_;

  rclcpp::Clock clock_{RCL_ROS_TIME};

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr benchmark_pub_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr ack_sub_;
  rclcpp::TimerBase::SharedPtr publish_timer_;
  rclcpp::TimerBase::SharedPtr stats_timer_;

  std::optional<rclcpp::Time> last_publish_time_;

  size_t seq_   = 0;
  size_t count_ = 0;
  double sum_ms_ = 0.0;
  double min_ms_ = std::numeric_limits<double>::max();
  double max_ms_ = 0.0;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<TopicLatencyBenchmarkNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
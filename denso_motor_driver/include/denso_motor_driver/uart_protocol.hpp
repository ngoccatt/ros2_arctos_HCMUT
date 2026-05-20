// uart_protocol.h
#ifndef UART_PROTOCOL_H_
#define UART_PROTOCOL_H_

#include "serial/serial.h"
#include <string>
#include <vector>
#include <queue>

#define DELIMITER   ","

namespace denso_motor_driver {

/**
 * @brief UART communication protocol handler for motor control and feedback
 */
class UartProtocol
{
public:
    /// @brief Default constructor
    UartProtocol() = default;

    /// @brief Constructor with serial port configuration
    explicit UartProtocol(const std::string &serial_device, int32_t baud_rate, int32_t timeout_ms)
        : serial_conn_(serial_device, baud_rate, serial::Timeout::simpleTimeout(timeout_ms))
    {}

    /// @brief Default destructor
    ~UartProtocol() = default;

    /// @brief Configure and open serial connection with specified parameters
    void setup(const std::string &serial_device, int32_t baud_rate, int32_t timeout_ms);
    
    /// @brief Check if serial connection is established and active
    bool connected() const { return serial_conn_.isOpen(); }

    /// flush the serial connection buffers to maintain stable communication.
    bool flush();

    /// @brief Read incoming UART data and store in receive buffer
    void readToBuffer(bool debug);
    
    /// @brief Get oldest message from buffer (FIFO) and remove it
    std::string getFromBuffer();

    /// @brief Decode received message string into position values vector, return true for success decode.
    /// If with_length is true, expects format "payload#LEN" and validates payload length.
    bool decodeMessage(const std::string data, std::vector<double> &axes, bool with_length = false);
    
    /// @brief Format position vector into message string and send via UART.
    /// If with_length is true, appends "#LEN" where LEN is the payload character count.
    bool sendPosition(std::vector<double> &positions, bool with_length = false);
    
    /// @brief Send empty message (carriage return) as keep-alive or wake-up signal
    bool sendEmptyMsg();

    /// @brief Low-level message transmission helper function
    bool sendMsg(const std::string &msg_to_send);

    /// @brief Low-level message transmission helper function appending EOL
    bool sendMsgWithCLRF(const std::string &msg_to_send_without_eol);
    
private:
    /// @brief Serial connection object for UART communication
    serial::Serial serial_conn_;
    
    /// @brief FIFO buffer queue for storing received messages
    std::queue<std::string> rev_buffer_;
    

};

} // namespace denso_motor_driver

#endif  //UART_PROTOCOL_H_

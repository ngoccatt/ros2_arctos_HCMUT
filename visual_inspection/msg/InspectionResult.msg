std_msgs/Header header
string label        # PASS | FAIL
int32 class_id      # 0=FAIL  1=PASS  (matches model_metadata.json class_names order)
float32 confidence
float32 latency_ms
float64 capture_time_unix  # Unix epoch when the camera frame was grabbed (for pipe latency)

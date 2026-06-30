std_msgs/Header header
string  label             # fist | open | point | thumbs_up | none
int32   class_id          # index into model class array
float32 confidence        # [0.0, 1.0] from softmax output
float32 latency_ms        # model inference time (ms, measured in backend)
float64 capture_time_unix # Unix epoch (s) when camera frame was grabbed

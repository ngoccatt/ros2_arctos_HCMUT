# Kế hoạch viết Chương 1 và Chương 2 – Luận văn thạc sĩ

## Context

Luận văn về **hệ thống điều khiển cánh tay robot Denso VS-6577 từ xa qua kính Meta Quest 3**, dựa trên ROS2/ros2-control + MoveIt2 + Unity 6. Hai chapter đầu cần được viết lại hoàn chỉnh:

- `Introduction.tex` hiện tại: quá sơ sài, chỉ khoảng 90 dòng, không có luận điểm học thuật, thiếu motivation rõ ràng.
- `research.tex` hiện tại: khoảng 40 dòng, đề cập vài paper nhưng phân tích nông, thiếu so sánh hệ thống, thiếu khoảng trống nghiên cứu (research gap).
- `draft3.tex`: phiên bản AI sinh ra – cấu trúc tốt, đủ học thuật, nhưng "quá đà" ở văn phong và một số khẳng định không chính xác. Thiếu 2 citation chưa có trong `ref.bib`: `wang2024genealogy` và `darvish2023teleoperation`.

**Mục tiêu**: Viết lại hoàn chỉnh hai file chapter với nội dung chi tiết, có citation đầy đủ, điểm mạnh/yếu của nghiên cứu liên quan, ưu thế của đề tài.

---

## Vấn đề cần xử lý trước

### Citations thiếu trong ref.bib
`draft3.tex` dùng `\cite{wang2024genealogy}` và `\cite{darvish2023teleoperation}` nhưng cả hai đều **không có** trong `ref.bib`.

**Giải pháp**: Thêm cả 2 entry vào `ref.bib`:
- `darvish2023teleoperation`: **"Teleoperation of Humanoid Robots: A Survey"** – Darvish et al., IEEE T-RO 2023, vol.39(3):1706–1727. File PDF có trong `ref_paper/Teleoperation of humanoid robots- A survey.pdf`. DOI: 10.1109/TRO.2023.3236952
- `wang2024genealogy`: **"A Genealogy of Human-Robot Collaboration"** – cần tìm bib entry chính xác khi implement. Tìm trên Google Scholar / CrossRef với key "wang 2024 genealogy human-robot collaboration".

---

## Chương 1: GIỚI THIỆU TỔNG QUAN

**File**: `Thesis_Cat/ThesisChapters/Introduction.tex` (viết lại hoàn toàn)

### Cấu trúc đề xuất

#### 1.1 Bối cảnh: Xu hướng điều khiển robot từ xa trong Công nghiệp 4.0–5.0
**Nội dung chính:**
- Vai trò ngày càng quan trọng của cánh tay robot trong sản xuất thông minh
- Sự chuyển dịch từ tự động hóa hoàn toàn sang **Human-Robot Collaboration (HRC)**: AI chưa đủ tự chủ trong môi trường phi cấu trúc → cần con người can thiệp từ xa
- Ứng dụng teleoperation trong y tế (phẫu thuật từ xa), môi trường nguy hiểm (phóng xạ, gỡ bom), không gian vũ trụ
- **Đóng góp học thuật**: Đặt bối cảnh và tầm quan trọng của vấn đề
- Citations: `\cite{wang2024genealogy}`, `\cite{autolab2021telesurgery}`, `\cite{han2023survey}`, `\cite{vr-in-contruction}`, `\cite{darvish2023teleoperation}`

#### 1.2 Sự tiến hóa của giao diện điều khiển: Từ GUI 2D đến VR
**Nội dung chính:**
- Teach Pendant / GUI 2D: hạn chế nhận thức không gian 3D, tải nhận thức (cognitive load) cao
- VR/MR: nhận thức chiều sâu tự nhiên, điều khiển bằng cử chỉ tay trực quan hơn
- Bản sao số (Digital Twin): đồng bộ thời gian thực, cho phép người dùng quan sát và kiểm tra quỹ đạo trước khi thực thi
- Citations: `\cite{hetrick2020comparing}`, `\cite{chen2023comparing}`, `\cite{torrejon2026teleoperation}`, `\cite{naceri2021vicarios}`

#### 1.3 Động lực nghiên cứu và các thách thức công nghệ
**Ba rào cản chính** (tương ứng với 3 đóng góp của luận văn):

1. **Middleware ROS1 và quản lý băng thông kém**: Phần lớn hệ thống teleoperation hiện nay dùng ROS1 (Master/Slave). Không có QoS thời gian thực → nghẽn mạng khi truyền đồng thời kinematics tần số cao và video stream.
   - Citations: `\cite{kawshan2026digital}`, `\cite{doi:10.1126/scirobotics.abm6074}`

2. **Rào cản giao tiếp với bộ điều khiển công nghiệp RC5**: RC5 vận hành bằng ngôn ngữ lập trình PAC độc quyền của Denso và chỉ hỗ trợ giao tiếp ngoại vi qua cổng UART (115200 baud). Đây là giới hạn phần cứng đặt ra, không phải thiết kế cho real-time servoing → khó đồng bộ chính xác tốc độ điều khiển từ MoveIt-Servo với tốc độ đáp ứng cơ học thực tế của cánh tay. Ngưỡng chấp nhận được của độ trễ end-to-end cho VR là 150–200ms.
   - Citations: `\cite{luu2025enhancing}`, `\cite{reality-fusion}`

3. **Hạn chế hiệu năng của thiết bị VR thế hệ trước**: Quest 2, HTC Vive có hiệu năng phần cứng thấp hơn, dẫn đến ứng dụng VR chạy nặng nề hơn, khó đảm bảo FPS ổn định trong điều kiện đồng bộ dữ liệu robot thời gian thực. Meta Quest 3 với chip Snapdragon XR2 Gen 2 mang lại hiệu năng cao hơn đáng kể.
   - Citations: `\cite{chen2023comparing}`, `\cite{naceri2021vicarios}`

#### 1.4 Mục tiêu và đóng góp khoa học của luận văn
**Đây là phần quan trọng nhất của Chương 1 – cần viết rõ ràng, có thể đo lường được:**

- **CĐ1**: Xây dựng kiến trúc phần mềm ROS2 phân tầng rõ ràng (driver → hardware interface → ros2-control → MoveIt2 → application layer), đóng vai trò platform mở rộng, cho phép tích hợp thêm mô-đun mới mà không ảnh hưởng các tầng khác. Đây là bước chuyển công nghệ từ cách tiếp cận đặc thù sang kiến trúc chuẩn hóa dựa trên ros2-control.
- **CĐ2**: Phát triển ứng dụng Digital Twin thời gian thực trên Meta Quest 3 (Unity 6 + ROS-Sharp) với hiệu năng 66+ FPS standalone, không cần PC đồ họa đi kèm. Dùng URDF/CAD model sẵn có để render 3D robot, đồng bộ trạng thái qua Joint States + camera stream qua WebSocket.
- **CĐ3**: Giải quyết rào cản giao tiếp với phần cứng cũ bằng giao thức UART tùy chỉnh + cơ chế Ring Buffer. Cơ chế Trend Learning được thêm vào như giải pháp tạm thời để giảm thiểu giật lùi quỹ đạo (trajectory oscillation) do chênh lệch tần số điều khiển MoveIt-Servo và tốc độ đáp ứng thực tế của RC5 – đây là một vấn đề kỹ thuật chưa giải quyết triệt để và cần nghiên cứu tiếp.

#### 1.5 Bố cục luận văn
**Không chỉ liệt kê – mỗi chương cần nêu rõ nội dung chính và đóng góp học thuật (nếu có):**
- **Chương 1** (hiện tại): Bối cảnh, động lực, thách thức và đóng góp của luận văn.
- **Chương 2**: Phân tích chuyên sâu 4 nhóm nghiên cứu (giao diện, digital twin, middleware, haptic). Xác định khoảng trống nghiên cứu làm cơ sở cho hướng tiếp cận.
- **Chương 3**: Nền tảng lý thuyết (động học robot, ROS2/DDS, ros2-control, MoveIt2, Unity/ROS-Sharp, UART protocol). Cung cấp kiến thức nền để đọc hiểu thiết kế.
- **Chương 4**: Thiết kế và hiện thực toàn bộ hệ thống (3 tầng: RC5/UART, ROS2 architecture, VR application). Trình bày chi tiết 3 đóng góp kỹ thuật CĐ1/CĐ2/CĐ3. **Đóng góp**: mô tả kiến trúc và giải pháp engineering mới.
- **Chương 5**: Kết quả thực nghiệm và đánh giá (latency benchmark, FPS, UART error rate, Gazebo simulation). **Đóng góp**: dữ liệu định lượng về hiệu năng hệ thống.
- **Chương 6**: Tổng kết và hướng phát triển (giải quyết hoàn toàn vấn đề đồng bộ RC5, cải thiện Trend Learning, tích hợp camera streaming, haptic feedback).

---

## Chương 2: CÁC NGHIÊN CỨU LIÊN QUAN VÀ PHÂN TÍCH KHOẢNG TRỐNG

**File**: `Thesis_Cat/ThesisChapters/research.tex` (viết lại hoàn toàn)

### Cấu trúc đề xuất

#### 2.1 Phân tích giao diện điều khiển robot từ xa
**Đề cập**: GUI 2D, hand gestures, VR controllers, mixed reality

**Nội dung chính + điểm mạnh/yếu:**
- `chen2023comparing` – So sánh 3 phương thức (GUI/hand/VR) trên JAKA Minicobo. **Mạnh**: dữ liệu thực nghiệm 16 người dùng, task time được đo lường khách quan. **Yếu**: dùng Oculus Quest 2 (cũ), ROS1, nhiệm vụ (câu cá) đơn giản, không đánh giá với robot công nghiệp real-world.
- `hetrick2020comparing` – So sánh trajectory-based vs. goal-based control trên Baxter/HTC Vive. **Mạnh**: phân tích cognitive load và workload. **Yếu**: robot 2 tay, không phổ biến với single-arm industrial context.
- `su2022mixed` – Mixed Reality + imitation-based mapping. **Mạnh**: ánh xạ cử chỉ tay tự nhiên sang robot. **Yếu**: latency cao do MR processing, cần PC mạnh.
- `zhang2023research` – 5D collaboration VR system (bao gồm force/haptic). **Mạnh**: tích hợp đa modal. **Yếu**: hardware đặc thù, không open-source.

**Kết luận đoạn**: VR Controllers (tay cầm) cho kết quả tốt nhất về tốc độ và ổn định so với cử chỉ tay và GUI 2D → lý do luận văn chọn Meta Quest 3 với VR controllers (không dùng hand tracking).

#### 2.2 Tích hợp Bản sao số (Digital Twin) và nhận thức tình huống
**Đề cập**: Point Cloud, URDF-based digital twin, multi-camera, teleporting viewpoint

**Nội dung chính + điểm mạnh/yếu:**
- `naceri2021vicarios` – Vicarios: teleporting + point cloud trên HTC Vive. **Mạnh**: góc nhìn linh hoạt, camera occlusion được giải quyết. **Yếu**: ROS1 + ROSBridge gây bottleneck, point cloud rendering đòi hỏi PC đồ họa mạnh.
- `multi-view` – AR multi-view merging (ZED + RealSense). **Mạnh**: Picture-in-Picture + Depth Projection giải quyết occlusion. **Yếu**: PiP không thiết kế tốt làm tăng cognitive load.
- `torrejon2026teleoperation` – Point Cloud >1M điểm, Unreal 5.6. **Mạnh**: hình ảnh môi trường thực cực kỳ chân thực. **Yếu**: cần RTX 3070+, latency 190ms, không standalone, quá tải đồ họa.
- `kawshan2026digital` – Unity-ROS1 digital twin với JetCobot. **Mạnh**: benchmark latency đầy đủ (144ms end-to-end). **Yếu**: ROS1 Master/Slave bottleneck được xác nhận.
- `singh2025comparative` – So sánh Digital Twin trong Unity vs. Gazebo. **Mạnh**: phân tích học thuật về simulation fidelity. **Yếu**: chỉ mô phỏng, không có real hardware control loop.
- `ali2025digital` – ROS2 + Digital Twin cho Reinforcement Learning. **Mạnh**: dùng ROS2 DDS thay cho ROS1. **Yếu**: offline training mode, không dùng cho interactive VR operator.

**Phân tích trade-off của luận văn**: Luận văn sử dụng Digital Twin đơn giản – URDF/CAD model được load sẵn trong Quest 3, đồng bộ Joint States và camera stream qua WebSocket. Đây là cách tiếp cận **lightweight và pragmatic**, giúp chạy standalone trên Quest 3 đạt 66.1 FPS, 60% GPU load. Tuy nhiên, cần thẳng thắn nhìn nhận: các nghiên cứu dùng Point Cloud (Naceri, Torrejón) cung cấp **nhận thức tình huống phong phú hơn** (thấy được vật thể 3D xung quanh), còn luận văn chỉ hiển thị mô hình robot và camera 2D. Ưu điểm của luận văn là **tính khả thi và hiệu năng standalone** trong bối cảnh hardware sẵn có, không phải về độ phong phú của digital twin.

#### 2.3 Tối ưu hóa Middleware và Quản lý Độ trễ
**Đề cập**: ROS1 vs ROS2, DDS, QoS, ROSBridge, bandwidth management

**Nội dung chính:**
- `kawshan2026digital` – Latency ROS1 Unity→Robot 144ms, xác nhận bottleneck của Master/Slave.
- `luu2025enhancing` – Teleoperation trong Industrial IoT, phân tích network impact. **Mạnh**: xem xét từ góc độ IoT infrastructure. **Yếu**: không có hardware interface chuẩn như ros2-control.
- `ali2025digital` – ROS2 DDS cho Digital Twin RL. Đặt tiền đề cho ROS2.
- `reality-fusion` – 3DGS streaming cho mobile robot. **Mạnh**: chất lượng hình ảnh cao. **Yếu**: 3DGS không phù hợp với static industrial arm.
- `doi:10.1126/scirobotics.abm6074` – Macenski et al. (2022), ROS2 design/architecture paper. Cơ sở kỹ thuật cho lựa chọn ROS2 DDS.

**Điểm mạnh luận văn**: Kết hợp ros2-control + MoveIt2 với VR interactive operator trên robot công nghiệp thực. DDS tự nhiên phân luồng: Camera stream (bandwidth cao) tách biệt khỏi Joint States (frequency cao), đảm bảo real-time không bị ảnh hưởng bởi video load.

#### 2.4 Haptic Feedback và Phản hồi cảm giác
**Đề cập**: haptic gloves, Force/Torque sensors, visual feedback compensation

**Nội dung chính + điểm mạnh/yếu:**
- `xu2025immersive` – Bimanual VR + Dexmo haptic glove. **Mạnh**: phản hồi xúc giác thực sự, tăng độ chính xác lắp ráp tinh vi. **Yếu**: thiết bị Dexmo đắt tiền, cần F/T sensor trên robot, thêm latency xử lý.
- `papakonstantinou2025effect` – Haptic glove cho single-arm. **Mạnh**: phân tích định lượng tác động của xúc giác. **Yếu**: cần F/T sensor gắn trực tiếp vào robot.
- `arclab2025beavr` – BEAVR: bimanual accessible VR teleoperation. **Mạnh**: open-source, đa nền tảng. **Yếu**: dùng robot nghiên cứu, không phải industrial robot có controller đời cũ.

**Lý do luận văn không dùng haptic**: Denso VS-6577/RC5 không trang bị F/T sensor tinh vi và chi phí tích hợp cao. Thay vào đó, tập trung tối ưu phản hồi thị giác (visual feedback) qua Digital Twin thời gian thực và camera stream đa luồng – dùng thị giác bù đắp xúc giác, phù hợp với điều kiện thực tế và kinh tế của đề tài.

#### 2.5 Bảng tổng hợp so sánh các nghiên cứu

Bảng LaTeX `\begin{table}...\end{table}` với 7 hàng (6 nghiên cứu + luận văn), các cột: Tác giả/Năm | Robot | Middleware | VR Device | Điểm mạnh | Hạn chế / Khác biệt với luận văn.

Các nghiên cứu đưa vào bảng:
- Chen et al. (2023) `chen2023comparing`
- Naceri et al. (2021) `naceri2021vicarios`
- Torrejón et al. (2026) `torrejon2026teleoperation`
- Xu et al. (2025) `xu2025immersive`
- Kawshan & Peng (2026) `kawshan2026digital`
- Luu et al. (2025) `luu2025enhancing`
- **Luận văn hiện tại** (Denso VS-6577 + ROS2 + Quest 3)

#### 2.6 Tổng kết: Khoảng trống nghiên cứu và định hướng
Tóm lược 3 research gaps mà luận văn nhắm đến:
1. Phần lớn công trình dùng ROS1 → bottleneck bandwidth → luận văn dùng ROS2 DDS
2. Digital Twin phụ thuộc Point Cloud nặng và PC đồ họa → luận văn dùng URDF lightweight + WebSocket
3. Chưa có công trình nào tích hợp full-stack VR-to-RC5 trên robot công nghiệp đời cũ không hỗ trợ real-time API → luận văn giải quyết bằng UART protocol + Ring Buffer + Trend Learning (giải pháp tạm thời đang tiếp tục hoàn thiện)

---

## Lưu ý chính xác kỹ thuật (từ feedback)

1. **RC5 không phải "designed for offline"**: Cần diễn đạt đúng – RC5 có khả năng điều khiển cánh tay rất chính xác, nhưng **giao tiếp từ bên ngoài bị giới hạn**: chỉ hỗ trợ ngôn ngữ PAC độc quyền của Denso (cần license) và cổng ngoại vi UART tốc độ thấp. Không phải vấn đề "offline" mà là **thiếu API ngoại vi thời gian thực linh hoạt**.

2. **Quest 3 được chọn vì hiệu năng**, không phải tính năng passthrough: Chip Snapdragon XR2 Gen 2 cho phép chạy ứng dụng Unity phức tạp ở FPS cao, standalone. Passthrough không được sử dụng trong đề tài này.

3. **Trend Learning là giải pháp tạm thời**: Do ros2-control chưa được đồng bộ hoàn toàn với thiết bị thật (chu kỳ điều khiển MoveIt-Servo nhanh hơn tốc độ đáp ứng RC5), cánh tay bị giật lùi khi nhận lệnh mới. Trend Learning giảm thiểu hiện tượng này nhưng chưa triệt để – đây là vấn đề mở cho nghiên cứu tiếp.

---

## Các file cần chỉnh sửa

| File | Hành động |
|------|-----------|
| `Thesis_Cat/ThesisChapters/Introduction.tex` | Viết lại hoàn toàn (~150-200 dòng LaTeX) |
| `Thesis_Cat/ThesisChapters/research.tex` | Viết lại hoàn toàn (~200-250 dòng LaTeX) |
| `Thesis_Cat/ref.bib` | Thêm 2 entry: `darvish2023teleoperation` + `wang2024genealogy` |

---

## Hướng dẫn văn phong

- **Không "quá đà"**: Tránh từ ngữ cực đoan như "triệt để", "vượt trội hoàn toàn". Dùng ngôn ngữ học thuật đo lường được ("đạt 66.1 FPS", "giảm độ trễ xuống dưới 150ms").
- **Có citation tại mỗi luận điểm**: Không đưa ra nhận định không có nguồn.
- **Phân tích có chiều sâu**: Mỗi paper: 2-3 câu về điểm mạnh VÀ điểm yếu cụ thể, liên kết với lý do luận văn làm khác/tốt hơn.
- **Trung thực về hạn chế**: Trend Learning là giải pháp tạm thời, vấn đề đồng bộ RC5 chưa giải quyết triệt để → phản ánh đúng trong text.
- **Tiếng Việt học thuật**: Thuật ngữ kỹ thuật giữ tiếng Anh (ros2-control, MoveIt2, Digital Twin, latency, QoS, DDS).

---

## Kiểm tra sau khi viết

1. Compile `ThesisReport.tex` bằng pdflatex/xelatex → không có lỗi citation undefined
2. Xác nhận tất cả `\cite{...}` trong 2 chapter mới đều có entry trong `ref.bib`
3. Kiểm tra tính nhất quán với Chương 3, 4, 5 (đặc biệt mô tả CĐ1/CĐ2/CĐ3)
4. Kiểm tra bảng LaTeX render đúng với `resizebox`

## Quan trọng!!

1. TUYỆT ĐỐI KHÔNG SỬ DỤNG CÁC HÀNH ĐỘNG CẦN PHẢI DÙNG "VISION" NHƯ ĐỌC FILE PDF. nếu cần truy cập tài liệu, tìm trên mạng hoặc tìm cách khác. Nếu không được thì khỏi luôn

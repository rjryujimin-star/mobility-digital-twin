import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# 1. 아두이노 시리얼 포트 연결 (너의 포트인 COM5, 속도 115200 설정)
try:
    py_serial = serial.Serial(port='COM5', baudrate=115200, timeout=1)
except Exception as e:
    print(f"포트 연결 실패! 아두이노 시리얼 모니터 창이 켜져 있는지 확인하세요.\n에러 내용: {e}")
    exit()

# 실시간 데이터를 저장할 리스트 변수들
raw_roll_list = []      # 필터 전 노이즈 데이터
filtered_roll_list = [] # 상보필터 적용 후 데이터
x_time_axis = []        # X축 시간축 역할을 할 카운터
count = 0

# matplotlib 그래프 창 초기 설정
fig, ax = plt.subplots(figsize=(10, 5))

# 필터 전(Raw)은 노이즈를 강조하기 위해 흐린 회색 점선으로 설정
line_raw, = ax.plot([], [], label='Raw Roll (Noise-heavy Accel)', color='gray', alpha=0.6, linestyle='--')
# 필터 후(Filtered)는 보정된 결과를 강조하기 위해 진한 빨간색 실선으로 설정
line_filtered, = ax.plot([], [], label='Filtered Roll (Complementary Filter)', color='red', linewidth=2)

ax.legend(loc='upper right')
ax.set_ylim(-90, 90)   # 차량 각도 가시 범위 (-90도 ~ 90도)
ax.set_xlim(0, 100)    # 화면에 보여줄 데이터 개수 (최근 100개)
ax.set_title("IMU Signal Processing: Raw vs Complementary Filtered", fontsize=12, fontweight='bold')
ax.set_xlabel("Time Frames (100Hz)")
ax.set_ylabel("Angle (Degrees)")

# 실시간으로 데이터를 읽어서 그래프를 갱신하는 함수
def update(frame):
    global count
    if py_serial.readable():
        # 아두이노가 보낸 데이터 한 줄 읽기
        line = py_serial.readline().decode('utf-8').strip()
        if line:
            try:
                # 아두이노 출력 포맷: accX, accY, rawRoll, filteredRoll, yaw, moving
                data = line.split(',')
                
                # 데이터가 정상적으로 6개 다 들어왔는지 검증
                if len(data) == 6:
                    raw_roll = float(data[2])       # 3번째 값: 필터 전 롤
                    filtered_roll = float(data[3])  # 4번째 값: 필터 후 롤
                    
                    # 리스트에 데이터 추가
                    raw_roll_list.append(raw_roll)
                    filtered_roll_list.append(filtered_roll)
                    x_time_axis.append(count)
                    count += 1
                    
                    # 최근 100개의 데이터만 유지하며 그래프가 왼쪽으로 흘러가게(Scrolling) 처리
                    if len(x_time_axis) > 100:
                        x_time_axis.pop(0)
                        raw_roll_list.pop(0)
                        filtered_roll_list.pop(0)
                        ax.set_xlim(x_time_axis[0], x_time_axis[-1])
                    
                    # 그래프 선 데이터 업데이트
                    line_raw.set_data(x_time_axis, raw_roll_list)
                    line_filtered.set_data(x_time_axis, filtered_roll_list)
                    
            except ValueError:
                pass # 데이터가 순간적으로 깨져서 들어오는 예외 처리
                
    return line_raw, line_filtered

# FuncAnimation을 통해 10ms 주기로 update 함수를 실행하여 실시간 플롯 구현
ani = FuncAnimation(fig, update, blit=True, interval=10, cache_frame_data=False)
plt.show()

# 창을 닫으면 시리얼 포트를 안전하게 닫아줌
py_serial.close()

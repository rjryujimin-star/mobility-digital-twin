import serial
import math
import tkinter as tk
from pythonosc.udp_client import SimpleUDPClient

# 1. 아두이노 시리얼 포트 연결 (COM3, 115200)
try:
    py_serial = serial.Serial(port='COM3', baudrate=115200, timeout=1)
except Exception as e:
    print(f"포트 연결 실패! 아두이노 창이나 이전 창을 닫았는지 확인하세요.\n에러: {e}")
    exit()

# 언리얼 엔진(OSC 플러그인, 8888 포트)으로 데이터를 보내는 클라이언트
osc_client = SimpleUDPClient("127.0.0.1", 8888)

# 2. Tkinter GUI 윈도우 생성 (파이썬 기본 내장)
root = tk.Tk()
root.title("Python Digital Twin Preview (Alternative)")
canvas = tk.Canvas(root, width=600, height=600, bg='black')
canvas.pack()

# 가상의 자동차 상자 좌표 설정 (중심점 300, 300)
CX, CY = 300, 300
HALF_W, HALF_H = 100, 40 # 자동차 상자 크기 (가로 200, 세로 80)

def rotate_rectangle(x, y, w, h, angle_deg):
    """상자를 각도(Yaw)에 따라 회전시키는 2D 연산 함수"""
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # 사각형의 네 꼭짓점 기준 좌표
    points = [(-w, -h), (w, -h), (w, h), (-w, h)]
    rotated_points = []
    
    # 회전 변환 행렬 적용
    for px, py in points:
        rx = x + (px * cos_a - py * sin_a)
        ry = y + (px * sin_a + py * cos_a)
        rotated_points.append(rx)
        rotated_points.append(ry)
    return rotated_points

# 실시간 데이터 루프 함수
def update_twin():
    if py_serial.readable():
        line = py_serial.readline().decode('utf-8').strip()
        if line:
            try:
                # 데이터 파싱: accX, accY, rawRoll, filteredRoll, yaw, moving
                data = line.split(',')
                if len(data) == 6:
                    acc_x = float(data[0])
                    acc_y = float(data[1])
                    raw_roll = float(data[2])
                    filtered_roll = float(data[3])
                    yaw = float(data[4])       # 5번째 값: 누적된 방향(Yaw)
                    is_moving = int(data[5])   # 6번째 값: 정지/이동 플래그

                    # 언리얼로 6개 값 그대로 전송 (주소: /rotation)
                    osc_client.send_message(
                        "/rotation",
                        [acc_x, acc_y, raw_roll, filtered_roll, yaw, is_moving]
                    )

                    # 화면 리셋
                    canvas.delete("all")
                    
                    # 회전된 자동차 상자 꼭짓점 구하기
                    rect_points = rotate_rectangle(CX, CY, HALF_W, HALF_H, -yaw)
                    
                    # 움직임 상태에 따른 자동차 색상 변경 (정지: 청록색, 이동: 빨간색)
                    car_color = "red" if is_moving == 1 else "cyan"
                    
                    # 3. 가상 자동차 그리기
                    canvas.create_polygon(rect_points, fill=car_color, outline="white", width=2)
                    
                    # 정면 방향 화살표 표시 (차량 헤드 방향)
                    head_rad = math.radians(-yaw)
                    hx = CX + (HALF_W + 30) * math.cos(head_rad)
                    hy = CY + (HALF_W + 30) * math.sin(head_rad)
                    canvas.create_line(CX, CY, hx, hy, fill="yellow", arrow=tk.LAST, width=3)
                    
                    # 텍스트 정보 표시
                    canvas.create_text(300, 50, text=f"Yaw (Direction): {yaw:.2f}°", fill="white", font=("Arial", 14))
                    canvas.create_text(300, 80, text=f"Status: {'MOVING' if is_moving == 1 else 'STOPPED'}", fill=car_color, font=("Arial", 14))
                    
            except ValueError:
                pass
                
    # 10ms 후에 이 함수를 다시 실행 (100Hz 루프 동기화)
    root.after(10, update_twin)

# 루프 시작
root.after(10, update_twin)
root.mainloop()
py_serial.close()

import serial
import socket
import time
from pythonosc.udp_client import SimpleUDPClient

# 1. UDP 소켓 설정 (로컬 호스트, 8888 포트)
UDP_IP = "127.0.0.1"
UDP_PORT = 8888
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client = SimpleUDPClient("127.0.0.1", 8888)

# 2. 아두이노 시리얼 포트 설정
SERIAL_PORT = 'COM5'
BAUD_RATE = 115200

print("=== 모빌리티 디지털 트윈 UDP 중계기 가동 ===")
print(f"목적지: {UDP_IP}:{UDP_PORT} (UDP)")

while True:
    try:
        # 시리얼 포트 연결 시도
        py_serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
        print(f"[{SERIAL_PORT}] 아두이노 연결 성공. 데이터 중계를 시작합니다.")
        
        while True:
            if py_serial.readable():
                # 데이터 수신 및 파싱 시간 측정 시작 (지연 실측용)
                start_time = time.time()
                
                line = py_serial.readline().decode('utf-8').strip()
                if line:
                    try:
                        # 아두이노 데이터 포맷: accX,accY,rawRoll,filteredRoll,yaw,moving
                        data = line.split(',')
                        
                        if len(data) == 6:
                            # 언리얼 전송용 패킷 가공 ("angleX,angleY,yaw,moving")
                            roll = data[3]
                            pitch = "0.0" # 피치는 가이드 스코프에 따라 기본값 처리하거나 가공 가능
                            yaw = data[4]
                            moving = data[5]
                            
                            packet = f"{roll},{pitch},{yaw},{moving}"
                            
                            # 3. UDP 전송
                            client.send_message("/car/data", [float(roll), float(pitch), float(yaw), float(moving)])
                            
                            # 4. 파이프라인 지연(Latency) 실측 계산
                            end_time = time.time()
                            latency_ms = (end_time - start_time) * 1000
                            
                            # 화면에 실시간 전송 상태 출력 (면접 자료용)
                            print(f"[전송 데이터] {packet} | 지연: {latency_ms:.2f}ms")
                            
                    except ValueError:
                        pass
                        
            time.sleep(0.001) # CPU 과점유 방지 (1ms 숏 딜레이)
            
    except serial.SerialException:
        # 아두이노 USB가 뽑히거나 연결이 끊겼을 때 튕기지 않고 재연결 대기 (예외 처리)
        print(f"\n[오류] 아두이노를 찾을 수 없습니다. 3초 후 포트({SERIAL_PORT}) 재연결을 시도합니다...")
        time.sleep(3)
    except KeyboardInterrupt:
        print("\n중계기를 안전하게 종료합니다.")
        break

if 'py_serial' in locals() and py_serial.is_open:
    py_serial.close()

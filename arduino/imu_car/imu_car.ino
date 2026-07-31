#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;

// 각도 및 필터용 변수
float roll = 0.0;
float pitch = 0.0;
float yaw = 0.0; // 자이로 Z축 적분으로 계산할 요(방향)

// 시간 계산용 변수 (dt 구하기용)
unsigned long lastTime;

void setup() {
  Serial.begin(115200); // 5단계 파이썬 중계기 및 3단계 그래프용 고속 통신
  while (!Serial) delay(10);

  // 센서 초기화 실패 시 무한 루프
  if (!mpu.begin()) {
    while (1) { delay(10); }
  }

  // 포트폴리오용 센서 정밀도 세팅
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);   // 가속도 범위 +-8G
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);       // 자이로 범위 +-500도/s
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);     // 자체 로우패스 필터 21Hz 세팅

  lastTime = millis();
}

void loop() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // 1. 샘플링 시간 간격(dt) 계산 (초 단위)
  unsigned long currentTime = millis();
  float dt = (currentTime - lastTime) / 1000.0;
  lastTime = currentTime;

  // 2. 가속도계 원시 값으로 롤(Roll)과 피치(Pitch) 계산 (atan2 공식)
  float accel_roll = atan2(a.acceleration.y, a.acceleration.z) * 180.0 / PI;
  float accel_pitch = atan2(-a.acceleration.x, sqrt(a.acceleration.y * a.acceleration.y + a.acceleration.z * a.acceleration.z)) * 180.0 / PI;

  // 3. 자이로 원시 값 변환 (라디안/s -> 도/s)
  float gyro_roll_rate = g.gyro.x * 180.0 / PI;
  float gyro_pitch_rate = g.gyro.y * 180.0 / PI;
  float gyro_yaw_rate = g.gyro.z * 180.0 / PI; // Z축 회전 속도

  // 4. 상보필터 적용 (가속도 안정성과 자이로 빠른 반응성 융합)
  roll = 0.98 * (roll + gyro_roll_rate * dt) + 0.02 * accel_roll;
  pitch = 0.98 * (pitch + gyro_pitch_rate * dt) + 0.02 * accel_pitch;

  // 5. 요(Yaw) 계산: 자이로 Z축 누적 적분 (가속도계로는 요를 구할 수 없음)
  // 정지 상태에서의 자이로 미세 노이즈(오프셋) 제거를 위한 데드존 처리
  if (abs(gyro_yaw_rate) > 0.5) { 
    yaw += gyro_yaw_rate * dt;
  }

  // 6. 가속도 크기 계산을 통한 이동(Moving) 상태 감지
  // 3축 가속도의 벡터 합성 총 크기를 구함 (정지 시 중력가속도인 약 9.8m/s^2 언저리가 나옴)
  float acc_magnitude = sqrt(a.acceleration.x * a.acceleration.x + 
                             a.acceleration.y * a.acceleration.y + 
                             a.acceleration.z * a.acceleration.z);
  
  // 정지 상태(9.8)에서 충격이나 움직임이 생겨 오차가 발생하면 moving 플래그 ON (문턱값 1.5 설정)
  int moving = (abs(acc_magnitude - 9.8) > 1.5) ? 1 : 0;

  // 7. 파이썬 파싱용 출력 포맷 (가이드 요구사항 반영)
  // "accX,accY,angleX,angleY,yaw,moving" 순서로 콤마 분리 출력
  Serial.print(a.acceleration.x); Serial.print(",");
  Serial.print(a.acceleration.y); Serial.print(",");
  Serial.print(accel_roll);       Serial.print(","); // 필터 전 Roll (3단계 그래프용)
  Serial.print(roll);             Serial.print(","); // 필터 후 Roll
  Serial.print(yaw);              Serial.print(","); // 적분한 Yaw
  Serial.println(moving);                            // 정지/이동 플래그 (0 또는 1)

  delay(10); // 100Hz 샘플링 주기를 맞추기 위한 10ms 딜레이
}
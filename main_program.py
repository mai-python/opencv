# import: 불러오기
import cv2           # 영상 처리
import numpy as np   # 수학 계산 및 배열 연산
import requests      # 서버와 http 통신
import time          # 일정 시간동안 대기 기능
import threading     # 여러 작업

# 해당 서버에서 명령을 가져옴
SERVER_URL = "https://api-server-huax.onrender.com/get_command" 

# class: 기능 형성, ex) class ObjectDetection은 객체 감지 기능
# self: class 안에서 자신을 가리킴, ex) self.capture = cv2.VideoCapture(0)은 현재 class가 사용하는 카메라 저장
# def: 함수 정의
# __init__: class가 생성될 때 자동으로 실행되는 초기 설정 함수, ex) 객체 탐지를 처음부터 ON or OFF할지 설정
# while True: 특정 조건이 만족할 때 까지 무한 반복
# requests.get: 서버에서 데이터를 가져옴
# cv2.putText(): 화면에 텍스트 출력

class ObjectDetection:
    def __init__(self): # 카메라, 변수, 서버 수신들의 초기설정
        self.capture = cv2.VideoCapture(0) # 카메라 사용(0-...)
        self.detect_objects = False # 객체 감지를 시작할지 말지 False(초기값)면 중지

        self.command_thread = threading.Thread(target=self.fetch_command)
        self.command_thread.daemon = True # 프로그램 종료 시 스레드 종료(스레드가 많아지면 오류발생)
        self.command_thread.start() #스레드 실행
        self.stable_frames = 5 # 같은 객체가 일정 횟수 이상 감지되야함
        self.stable_count = 0 # 감지된 횟수 초기화
        self.last_detected_circle = None # 마지막으로 감지된 원의 정보 저장
        self.last_valid_circle = None # 유효한 객체로 인정된 원의 정보 저장

    def fetch_command(self): # 서버에서 주기적으로 명령을 가져오는 함수
        while True:
            try:
                response = requests.get(SERVER_URL) # get(가져오기) 요청을 보냄
                command = response.json().get("action", "stop") # 서버에서 action 명령을 가져옴
                self.detect_objects = (command == "start") # start면 객체 감지 ON
                print(f"현재 서버 명령: {command}, detect_objects 상태: {self.detect_objects}")
                time.sleep(1) # 1초마다 서버에 요청
            except requests.exceptions.RequestException as e: # 서버연결 오류 시
                print(f"서버 연결 오류: {e}") 
                time.sleep(2) # 서버연결 2초 대기

    def start_detection(self): # 카메라를 통해 객체를 감지하는 함수
        while True:
            ret, frame = self.capture.read() # 카메라에서 frame 읽기
            if not ret: # frame을 읽지 못하면
                print("Error: 프레임을 읽어올 수 없습니다.")
                break 

            height, width = frame.shape[:2] # frame의 높이와 너비
            center_x, center_y = width // 2, height // 2 # 화면 중심 좌표 계산
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # frame을 그레이스케일로 변환
            gray_blurred = cv2.GaussianBlur(gray, (9, 9), 2) # 가우시안 블러 적용(noise제거)

            circles = cv2.HoughCircles( #hough 변환으로 circle 검출
                gray_blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=80, # gray_blurred: 흑백 이미지(노이즈 제거), dp=1.2: 해상도 비율(1보다 낮으면 정확도 향상, 크면 속도 향상), minDist=80: 원 간 최소 거리(값이 작으면 여러개 검출됨, 크면 멀리 떨어져있어야 검출)
                param1=50, param2=30, minRadius=5, maxRadius=100      # param1: Canny엣지 검출 임계값(값을 높이면 원 검출이 잘 안될 수 있음), param2: 원의 중심 감지 임계값(값이 작으면 더 많은 원 검출, 크면 더 정확한 원 검출)
            )                                                         # min/maxRadius: 검출할 최소/최대 반지름 크기 설정

            if self.detect_objects and circles is not None:
                circles = np.round(circles[0, :1]).astype("int") # 검출된 원의 좌표를 정수형(int)으로 변환
                for (x, y, r) in circles: 
                    cv2.circle(frame, (x, y), r, (0, 255, 0), 2) 

                    # 중심 위치 (십자가)
                    cv2.line(frame, (x - 10, y), (x + 10, y), (0, 255, 0), 2) # 가로
                    cv2.line(frame, (x, y - 10), (x, y + 10), (0, 255, 0), 2) # 세로

                    # 초록원 위치와 중심(십자가) 위치의 오차 값 출력
                    error_x = x - center_x
                    error_y = y - center_y
                    cv2.putText(frame, f"Error X: {error_x}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2) # Error X: {error_x}: 표시할 텍스트, (10,30): 텍스트 위치(x,y), cv2.FONT_HERSHEY_SIMPLEX: 폰트 스타일
                    cv2.putText(frame, f"Error Y: {error_y}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2) # 0.7: 글자 크기, (255, 255, 255): 색상, 2: 글자 두께
                   
                    # 원의 경계 좌표 설정(화면을 벗어나지 않도록 제한한 것)
                    x1, y1, x2, y2 = max(x - r, 0), max(y - r, 0), min(x + r, width), min(y + r, height)
                    # 감지된 원 내부의 영역(region of Interest) 추출
                    roi = gray[y1:y2, x1:x2]
                    # roi에서 Canny 엣지 검출을 이용해서 경계선 찾기
                    edges = cv2.Canny(roi, 50, 150, apertureSize=3)
                    # Hough 변환을 사용해 경계선에서 선 감지
                    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=30)
                    # 각도 초기값
                    angle_detected = 0
                    # 감지된 선이 있다면 각도 계산
                    if lines is not None:
                        angles = [] # 각도 저장
                        for line in lines:
                            rho, theta = line[0] # 감지된 선들의 각도를 저장할 parameter(값을 전달하는 변수)
                            deg = np.degrees(theta) # radian을 degree로 변환
                            # 90도를 초과하면 180도를 빼서 보정
                            if deg > 90:
                                deg = deg - 180
                            angles.append(deg)
                        # -45도에서 45도 사이의 각도만 필터링링
                        valid_angles = [a for a in angles if abs(a) < 45]
                        # 각도가 있다면 중앙값을 사용해 최종 각도로 설정
                        if valid_angles:
                            angle_detected = np.median(valid_angles)
                    # 감지된 각도 값을 화면에 표시
                    cv2.putText(frame, f"Error Angle: {angle_detected:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                # 이전 frame과 동일한 원이 감지되었는지 검증하여 안정성 향상
                if self.last_detected_circle is None or (x, y, r) == self.last_detected_circle:
                    self.stable_count += 1 # 같은 객체 +1
                else:
                    self.stable_count = 0 # 다르면 초기화
                # 객체 감지 기능 보정(일정 횟수 이상 같은 객체가 감지)
                if self.stable_count > self.stable_frames:
                    # 이전에 감지된 유효한 원 계속 추적적
                    self.last_valid_circle = (x, y, r)
                    print("Stable object detected")

                self.last_detected_circle = (x, y, r)
            else:
                if self.last_valid_circle is not None:
                    print("Tracking last valid object:", self.last_valid_circle)
            # 화면 중앙에 십자선 표시(객체 중심과 비교)
            cv2.line(frame, (center_x - 15, center_y), (center_x + 15, center_y), (255, 0, 0), 2)
            cv2.line(frame, (center_x, center_y - 15), (center_x, center_y + 15), (255, 0, 0), 2)
            # 이물질 감지 경고
            warning_detected = False
            edges = cv2.Canny(gray, 50, 150)
            # contours(윤곽선) 찾기
            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # 감지된 모든 윤곽선을 돌면서 이물질(삼각형) 감지
            for contour in contours:
                # 윤곽선을 단순화하여 꼭짓점 찾기
                approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                # 꼭짓점이 3개면 이물질(삼각형)로 판단
                if len(approx) == 3:
                    # 이물질을 빨간색으로 표시
                    cv2.drawContours(frame, [approx], 0, (0, 0, 255), 2)
                    # 경고 ON
                    warning_detected = True
            
            # 이물질이 감지된 경우 메시지 표시
            if warning_detected:
                cv2.putText(frame, "Warning: Triangle detected!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 255), 2)
            
            #ㅊ 최종 frame을 화면에 표시시
            cv2.imshow("Object Tracking", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'): # 'q' 누르면 종료
                break

        self.capture.release() # 카메라 작동 중지
        cv2.destroyAllWindows() # 창 닫기


# 파이썬 내에서만 구동 
if __name__ == "__main__":
    object_detection = ObjectDetection() 
    object_detection.start_detection()

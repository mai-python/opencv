# 필요한 라이브러리 불러오기
import requests  # Flask 서버와 통신하기 위해 사용
from kivy.app import App  # Kivy 애플리케이션을 만들기 위한 기본 클래스
from kivy.uix.boxlayout import BoxLayout  # UI 요소를 배치하는 레이아웃 클래스
from kivy.uix.button import Button  # 버튼을 만들기 위한 클래스
from kivy.uix.label import Label  # 텍스트를 표시하는 라벨 클래스
import json  # 데이터를 JSON 형식으로 변환하기 위해 사용

# 서버 주소
SERVER_URL = "https://api-server-huax.onrender.com/send_command"

# 애플리케이션의 메인 UI를 구성하는 class
class ControlApp(BoxLayout):
    def __init__(self, **kwargs):
        # 부모 클래스(BoxLayout)의 생성자 호출 (세로 방향 레이아웃 설정)
        super().__init__(orientation="vertical", **kwargs)

        # 현재 상태를 표시하는 레이블 (기본값: "standby")
        self.status_label = Label(text="state: standby", font_size=20)
        self.add_widget(self.status_label)  # UI에 레이블 추가

        # "operate" 버튼 생성 (장치를 작동시키는 버튼)
        start_button = Button(text="operate", font_size=24, size_hint=(1, 0.3))
        # 버튼을 클릭하면 send_command 함수가 실행되도록 연결
        start_button.bind(on_press=lambda x: self.send_command("start"))
        self.add_widget(start_button)  # UI에 버튼 추가

        # "pause" 버튼 생성 (장치를 멈추는 버튼)
        stop_button = Button(text="pause", font_size=24, size_hint=(1, 0.3))
        # 버튼을 클릭하면 send_command 함수가 실행되도록 연결
        stop_button.bind(on_press=lambda x: self.send_command("stop"))
        self.add_widget(stop_button)  # UI에 버튼 추가

    # ** Flask 서버로 명령을 보내는 함수 **
    def send_command(self, action):
        """
        사용자가 버튼을 누르면 해당 동작을 Flask 서버로 전송하는 함수
        action: "start" 또는 "stop" 문자열을 받아 서버로 전송
        """
        try:
            # 서버에 보낼 데이터를 JSON 형식으로 구성
            data = {"action": action}
            headers = {"Content-Type": "application/json"}  # 요청 헤더 설정

            # Flask 서버로 POST 요청을 보냄 (JSON 데이터 포함)
            response = requests.post(SERVER_URL, json=data, headers=headers)

            # 서버 응답이 성공적(HTTP 상태 코드 200)인지 확인
            if response.status_code == 200:
                # 서버에서 받은 응답(JSON 형식)을 파이썬 딕셔너리로 변환
                result = response.json()
                # 서버에서 받은 'action' 값을 UI에 표시
                self.status_label.text = f"state: {result.get('command', {}).get('action', 'error')}"
            else:
                # 오류 발생 시 상태 코드 표시
                self.status_label.text = f"Error: {response.status_code}"

        # 예외 처리: 네트워크 연결 오류
        except requests.exceptions.ConnectionError:
            self.status_label.text = "Connection Error"

        # 예외 처리: 요청 시간이 초과된 경우
        except requests.exceptions.Timeout:
            self.status_label.text = "Request Timed Out"

        # 예외 처리: 기타 요청 관련 오류
        except requests.exceptions.RequestException as e:
            self.status_label.text = f"Request Error: {str(e)}"

# ** Kivy 애플리케이션 실행 클래스 **
class RemoteControlApp(App):
    def build(self):
        # ControlApp 인스턴스를 생성하여 UI로 설정
        return ControlApp()

# ** 애플리케이션 실행 코드 **
if __name__ == "__main__":
    RemoteControlApp().run()

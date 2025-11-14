import json
from gtts import gTTS
from moviepy.editor import *
import os
import google.generativeai as genai
# ... (중략) ...
from openai import OpenAI
import requests
from PIL import Image
import numpy as np
from dotenv import load_dotenv # ◀◀◀ 1. dotenv import 추가

# .env 파일에서 환경 변수를 불러옵니다
load_dotenv() # ◀◀◀ 2. .env 파일 로드

# 3. os.getenv()를 사용해 키를 '개인 금고'(.env)에서 불러옵니다
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 4. 키가 제대로 로드되었는지 확인 (선택 사항이지만 추천)
if not OPENAI_API_KEY or not GEMINI_API_KEY:
    print("="*50)
    print("!!! 보안 오류 !!!")
    print("API 키를 .env 파일에서 찾을 수 없습니다.")
    print("프로젝트 폴더에 .env 파일을 만들고 키를 입력하세요.")
    print("="*50)
    exit() # 키가 없으면 프로그램 중지

JSON_INPUT_PATH = "output/sample_earnings.json"
# BACKGROUND_ASSET = "background.jpg" # 이 줄은 이제 필요 없으니 지워도 됩니다.

# --- 설정 ---
# 입력 JSON 파일 경로 (실제로는 main.py에서 생성된 파일을 지정)
JSON_INPUT_PATH = "output/sample_earnings.json"
# 사용할 배경 이미지 또는 영상 경로
BACKGROUND_ASSET = "background.jpg" 
# 사용할 폰트 (Windows는 'Malgun-Gothic', macOS는 'AppleGothic')
FONT_FILE = "AppleGothic"
# 결과물이 저장될 폴더
OUTPUT_DIR = "video_output"
# --- 설정 끝 ---

def load_data(json_path: str) -> dict:
    """JSON 파일을 읽어 데이터 반환"""
    print(f"[1] JSON 데이터 로딩 중... ({json_path})")
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_narration_script(data: dict) -> str:
    """JSON 데이터를 바탕으로 OpenAI API를 호출해 나레이션 대본 생성"""
    print("[2] OpenAI API (GPT)로 나레이션 대본 생성 중...")

    # 1. OpenAI 클라이언트 초기화 (이미지 생성과 동일)
    client = OpenAI(api_key=OPENAI_API_KEY)

    # 2. AI에게 보낼 프롬프트(지시서) 작성
    json_data_string = json.dumps(data, ensure_ascii=False, indent=2)

    prompt = f"""
    당신은 경제 뉴스를 전문으로 하는 AI 앵커입니다.
    내가 제공하는 기업 실적 JSON 데이터를 바탕으로, 20초 분량의 숏폼 뉴스 영상 대본을 작성해 주세요.
    
    [규칙]
    - 핵심적인 내용만 간결하게 전달해야 합니다.
    - 친근하지만 전문적인 뉴스 앵커 톤을 유지해 주세요.
    - 가장 중요한 실적(예: 영업이익 증가)을 강조해 주세요.
    - 감탄사나 불필요한 추측은 제외하고 사실 기반으로 작성해 주세요.

    [입력 데이터 (JSON)]
    {json_data_string}

    [대본 작성 시작]
    """

    # 3. API 호출 및 결과 반환
    try:
        # GPT-4o 또는 GPT-4-turbo 사용
        response = client.chat.completions.create(
            model="gpt-4o-mini", # ◀◀◀ gpt-4o-mini가 가장 빠르고 저렴합니다.
            messages=[
                {"role": "system", "content": "당신은 경제 뉴스 전문 앵커입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        script = response.choices[0].message.content
        return script.strip()
        
    except Exception as e:
        print(f"!!! OpenAI (GPT) API 호출 오류: {e}")
        return "오류: 대본 생성에 실패했습니다."


def create_audio(script: str, audio_path: str):
    """대본을 음성 파일(MP3)로 변환"""
    print(f"[3] 음성 파일 생성 중... ({audio_path})")
    tts = gTTS(text=script, lang='ko')
    tts.save(audio_path)

def create_video_scene(data: dict, audio_path: str, output_path: str):
    """MoviePy를 사용하여 영상 씬 생성 및 최종 영상 출력"""
    print("[4] MoviePy로 영상 생성 시작...")

    print("  [4-1] OpenAI DALL-E 3 API로 배경 이미지 생성 중...")
    try:
        # OpenAI 클라이언트 초기화
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # 이미지 프롬프트 생성 (JSON의 요약 제목 활용)
        image_prompt_raw = data.get("performance_summary", {}).get("summary_title", "stock market")
        
        # DALL-E가 잘 알아듣도록 프롬프트 가공
        image_prompt = f"A photorealistic image visualizing '{image_prompt_raw}'. High-tech, corporate, clean aesthetic, suitable for a news report."
        # 예: "A photorealistic image visualizing 'DS(반도체) 부문 실적 개선'. High-tech, corporate, clean aesthetic..."

        # DALL-E 3 API 호출
        response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1792",  # ◀ 숏폼(9:16) 비율. 1080x1920에 적합
            quality="standard", # 'hd'보다 저렴
            n=1               # ◀ 1장만 생성
        )
        
        image_url = response.data[0].url # 생성된 이미지의 URL
        
        # 2. 생성된 이미지 다운로드
        print(f"  [4-2] 생성된 이미지 다운로드... (URL: {image_url})")
        image_data = requests.get(image_url).content
        
        # 다운로드한 이미지를 임시 파일로 저장
        generated_bg_path = os.path.join(OUTPUT_DIR, "generated_background.jpg")
        with open(generated_bg_path, 'wb') as f:
            f.write(image_data)

    except Exception as e:
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"!!! AI 이미지 생성/다운로드 중 심각한 오류 발생 !!!")
        print(f"!!!               오류 원인 (OpenAI)             !!!")
        print(f"{e}") # ◀◀◀ OpenAI가 보낸 '진짜' 오류 메시지를 출력합니다.
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        generated_bg_path = None # 실패 시 None

    # 3. 오디오 및 배경 클립 로드
    audio_clip = AudioFileClip(audio_path)
    video_duration = audio_clip.duration + 1

    # 배경: AI 생성 이미지 또는 단색 클립 사용
    if generated_bg_path and os.path.exists(generated_bg_path):
        try:
            print("  [4-3] Pillow(PIL)로 이미지 리사이징 및 크롭 중...")
            # 1. Pillow로 이미지 열기
            pil_img = Image.open(generated_bg_path)
            
            # 2. 1080x1920 (숏폼) 비율에 맞게 리사이징 및 크롭
            # DALL-E 이미지(1024x1792)를 1080x1920 캔버스에 맞게 조정
            
            # 먼저 높이를 1920으로 리사이징 (너비는 비율에 맞게 1152가 됨)
            new_height = 1920
            new_width = int(pil_img.width * (new_height / pil_img.height))
            resized_img = pil_img.resize((new_width, new_height), Image.LANCZOS) # ANTIALIAS의 새 버전

            # 3. 중앙을 기준으로 1080 너비로 크롭
            target_width = 1080
            left = (new_width - target_width) / 2
            right = (new_width + target_width) / 2
            cropped_img = resized_img.crop((left, 0, right, new_height))
            
            # 4. MoviePy가 읽을 수 있도록 Numpy 배열로 변환
            frame = np.array(cropped_img)
            
            # 5. MoviePy 클립 생성
            bg_clip = ImageClip(frame, duration=video_duration)

        except Exception as e:
            print(f"!!! 이미지 리사이징/크롭 중 오류 발생: {e}. 단색 배경으로 대체합니다.")
            bg_clip = ColorClip(size=(1080, 1920), color=(20, 20, 40), duration=video_duration)
    else:
        bg_clip = ColorClip(size=(1080, 1920), color=(20, 20, 40), duration=video_duration)
        if generated_bg_path: # 경로는 있는데 파일이 없는 경우
             print("배경 이미지를 찾을 수 없어 단색 배경을 사용합니다.")
    
    bg_clip = bg_clip.set_audio(audio_clip)

    # 2. 텍스트 클립 생성
    info = data.get("report_info", {})
    summary = data.get("performance_summary", {})
    financials_list = data.get("financials", {}).get("consolidated_statement", [])
    
    company_name = info.get("company_name", "기업 리포트").replace("주식회사", "")
    period = info.get("period", "")
    key_message = summary.get("key_message", "")

    # 텍스트 포맷팅
    financials_text = ""
    for item in financials_list:
        name = item.get("item")
        amount = item.get("current_period_amount")
        growth = item.get("yoy_growth_rate")
        financials_text += f"{name}: {amount}원 ({growth})\n"

    # 3. 텍스트 클립 리스트 생성 (등장 시간, 내용, 위치 등 설정)
    clips_to_compose = [bg_clip]
    
    # ... (create_video_scene 함수 내부) ...

    # 3. 텍스트 클립 리스트 생성 (등장 시간, 내용, 위치 등 설정)
    clips_to_compose = [bg_clip]
    
    # (Scene 1) 타이틀
    # 1. bg_color='black' 추가
    title_clip = TextClip(f"{company_name}\n{period} 실적", fontsize=80, color='white', font=FONT_FILE, size=(900, 400), method='caption', bg_color='black')
    # 2. .set_opacity(0.6) 추가
    title_clip = title_clip.set_position('center').set_duration(4).set_start(1).crossfadein(0.5).set_opacity(0.6)
    clips_to_compose.append(title_clip)
    
    # (Scene 2) 핵심 메시지
    # 1. bg_color='black' 추가
    msg_clip = TextClip(key_message, fontsize=60, color='yellow', font=FONT_FILE, size=(1000, 500), method='caption', bg_color='black')
    # 2. .set_opacity(0.6) 추가
    msg_clip = msg_clip.set_position('center').set_duration(5).set_start(5).crossfadein(0.5).set_opacity(0.6)
    clips_to_compose.append(msg_clip)
    
    # (Scene 3) 재무 하이라이트
    # 1. bg_color='black' 추가
    financials_clip = TextClip(financials_text, fontsize=55, color='white', font=FONT_FILE, align='West', size=(1000, 600), method='caption', bg_color='black')
    # 2. .set_opacity(0.6) 추가
    financials_clip = financials_clip.set_position('center').set_duration(video_duration - 10).set_start(10).crossfadein(0.5).set_opacity(0.6)
    clips_to_compose.append(financials_clip)
    
    # 4. 모든 클립 합성
    # ... (이하 동일) ...
    
    # 4. 모든 클립 합성
    final_clip = CompositeVideoClip(clips_to_compose, size=(1080, 1920)) # 숏폼 사이즈
    
    # 5. 영상 파일로 렌더링
    print(f"[5] 최종 영상 파일 렌더링 중... ({output_path})")
    final_clip.write_videofile(output_path, codec='libx264', fps=24, audio_codec='aac')
    print("✨ 영상 생성 완료!")


def main():
    """메인 실행 함수"""
    # 0. 샘플 JSON 파일 생성 (테스트용)
    if not os.path.exists(JSON_INPUT_PATH):
        print("입력 JSON 파일을 찾을 수 없어, 테스트용 샘플 파일을 생성합니다.")
        sample_data = { "report_info": { "company_name": "삼성전자주식회사", "period": "2025년 반기" }, "performance_summary": { "summary_title": "반도체 실적 개선", "key_message": "영업이익 25% 증가, 어닝 서프라이즈!" }, "financials": { "consolidated_statement": [ { "item": "매출액", "current_period_amount": "145조 4,634억", "yoy_growth_rate": "+5.0%" }, { "item": "영업이익", "current_period_amount": "15조 4,872억", "yoy_growth_rate": "+25.0%" } ] } }
        os.makedirs(os.path.dirname(JSON_INPUT_PATH), exist_ok=True)
        with open(JSON_INPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=4)
            
    # 출력 디렉토리 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 실행 파이프라인
    data = load_data(JSON_INPUT_PATH)
    
    file_basename = os.path.splitext(os.path.basename(JSON_INPUT_PATH))[0]
    audio_path = os.path.join(OUTPUT_DIR, f"{file_basename}.mp3")
    output_video_path = os.path.join(OUTPUT_DIR, f"{file_basename}.mp4")
    
    script = generate_narration_script(data)
    print(f"\n--- 생성된 대본 ---\n{script}\n---------------------\n")
    
    create_audio(script, audio_path)
    create_video_scene(data, audio_path, output_video_path)


if __name__ == "__main__":
    main()
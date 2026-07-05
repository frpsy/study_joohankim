import yt_dlp
import re

def get_youtube_urls(url, output_file="youtube_urls.txt"):
    # 입력된 주소에 list= (재생목록 ID)가 포함되어 있다면, 안전하게 재생목록 전용 주소로 변환합니다.
    if 'list=' in url and 'playlist?list=' not in url:
        playlist_id = re.search(r'list=([^&]+)', url)
        if playlist_id:
            url = f"https://www.youtube.com/playlist?list={playlist_id.group(1)}"

    ydl_opts = {
        'extract_flat': True,         # 영상 데이터를 다운로드하지 않고 목록(메타데이터)만 추출
        'ignoreerrors': True,         # 에러 발생 시 건너뛰기
        'noplaylist': False,          # 재생목록 전체를 가져오도록 강제 설정 (핵심 변경 사항)
    }
    
    print(f"\n[안내] 재생목록에서 영상을 분석 중입니다: {url}")
    print("[안내] 영상이 많을 경우 시간이 다소 소요될 수 있습니다...\n")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(url, download=False)
            
            if not result:
                print("[실패] 정보를 가져오지 못했습니다. 주소를 확인해주세요.")
                return

            video_urls = []
            
            # 재생목록 구조 처리
            if 'entries' in result:
                entries = result['entries']
            elif result.get('_type') == 'playlist':
                entries = result.get('entries', [])
            else:
                entries = [result]

            for entry in entries:
                if entry:
                    if entry.get('_type') in ['playlist', 'multi_video']:
                        continue

                    video_id = entry.get('id') or entry.get('url')
                    if video_id:
                        if str(video_id).startswith('http'):
                            video_url = video_id
                        else:
                            # 채널의 "재생목록" 탭 등은 _type이 'url'로 나와 위 필터를 통과하지만
                            # id가 영상이 아니라 재생목록 ID(11자가 아님)이므로 여기서 걸러냅니다.
                            if not re.fullmatch(r'[\w-]{11}', str(video_id)):
                                continue
                            video_url = f"https://www.youtube.com/watch?v={video_id}"

                        if video_url not in video_urls:
                            video_urls.append(video_url)
            
            if video_urls:
                with open(output_file, "w", encoding="utf-8") as f:
                    for video_url in video_urls:
                        f.write(video_url + "\n")
                
                print("-" * 50)
                print(f"★ 수집 완료! 총 {len(video_urls)}개의 재생목록 영상 URL이 '{output_file}'에 저장되었습니다.")
                print("-" * 50)
            else:
                print("[실패] 추출된 영상 URL이 없습니다. 주소 유형을 확인해주세요.")
                
        except Exception as e:
            print(f"[오류] 데이터 추출 중 문제가 발생했습니다: {e}")

if __name__ == "__main__":
    user_input = input("수집할 유튜브 재생목록(또는 채널) 주소를 입력하세요: ").strip()
    
    if user_input:
        get_youtube_urls(user_input)
    else:
        print("[종료] 입력된 주소가 없어 프로그램을 종료합니다.")
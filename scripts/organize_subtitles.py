#!/usr/bin/env python3
"""
김주환 교수 채널 자막 파일 주제별 폴더 정리 스크립트
=====================================================

기능:
  - subtitles 폴더 안의 TXT 자막 파일들을 제목 키워드 기준으로
    주제별 하위 폴더로 자동 이동/정리합니다.
  - 이미 정리된 파일을 다시 실행해도 안전하도록 '복사'가 아닌 '이동'이며,
    같은 이름의 파일이 있으면 건너뜁니다.
  - 어떤 카테고리에도 속하지 않는 파일은 '기타' 폴더로 모으고,
    실행 후 목록을 출력해줍니다 (수동으로 확인하실 수 있도록).

사용법 (저장소 루트에서 실행):
  python3 scripts/organize_subtitles.py --dir authors/김주환/subtitles

옵션:
  --dir       정리할 폴더 경로 (기본값: ./subtitles)
  --dry-run   실제로 이동하지 않고, 어떻게 분류될지만 미리 보여줌

참고:
  이 스크립트는 김주환 교수 채널 기준 카테고리로 작성되어 있습니다.
  다른 저자/교수님의 강의를 정리할 때는 CATEGORIES를 해당 주제에 맞게
  수정하거나, authors/<이름>/ 폴더별로 스크립트를 복사해 커스터마이징하세요.
"""

import argparse
import shutil
from pathlib import Path


# 카테고리별 키워드 정의 (순서가 중요합니다 - 위에서부터 먼저 매칭)
# 하나의 파일이 여러 키워드에 걸릴 경우, 먼저 나열된 카테고리로 분류됩니다.
CATEGORIES = [
    ("01_수면유도명상", [
        "수면유도 명상",
    ]),
    ("02_마음근력_회복탄력성", [
        "마음근력", "회복탄력성", "그릿", "그릿(", "성취역량", "동기부여",
        "자기불리화", "인정중독", "인정에 의존",
    ]),
    ("03_뇌과학_의식", [
        "뇌", "의식", "신경가소성", "도파민", "뇌파", "감마파", "미토콘드리아",
        "능동적 추론", "예측모형", "마코프 블랭킷",
    ]),
    ("04_감정_심리", [
        "불안", "분노", "용서", "사랑", "감사", "연민", "두려움", "감정",
        "트라우마", "EMDR", "최면", "플라시보",
    ]),
    ("05_명상이론_전통", [
        "명상", "아나빠나사띠", "니미따", "불교", "유교", "간화선", "돈오점수",
        "알아차림", "메따", "위빠사나",
    ]),
    ("06_철학_사상", [
        "장자", "화엄", "공(空)", "연기(", "자유 의지", "이기적 유전자",
        "중관사상", "체화된 마음", "신라", "지눌",
    ]),
    ("07_몸_신체_감각", [
        "소매틱", "미주신경", "고유감각", "내부감각", "알로스태시스",
        "움직임", "호흡", "심상 훈련",
    ]),
    ("08_사회_미디어_기호학", [
        "기호", "브랜드", "대중매체", "디지털", "미술", "세뇌", "휴대폰",
    ]),
    ("09_자녀_교육_학습", [
        "아이", "공부", "학습", "시험", "어린이집",
    ]),
    ("10_관계_소통", [
        "내면소통", "인간관계", "부부", "연인", "커뮤니케이션", "엄마",
        "친절", "무례",
    ]),
    ("11_건강_수면_영양", [
        "숙면", "잠 잘 자는 법", "식사", "운동법", "먹어야",
    ]),
]

OTHER_FOLDER = "12_기타"

# 자막이 아닌 부산물 파일(다운로더가 생성하는 실패 로그 등)은 분류 대상에서 제외합니다.
IGNORE_FILES = {"failed_urls.txt"}


def classify(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    for folder_name, keywords in CATEGORIES:
        for kw in keywords:
            if kw in stem:
                return folder_name
    return OTHER_FOLDER


def main():
    parser = argparse.ArgumentParser(description="자막 TXT 파일을 주제별 폴더로 정리합니다.")
    parser.add_argument("--dir", default="./subtitles", help="정리할 폴더 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제로 이동하지 않고 미리보기만 함")
    args = parser.parse_args()

    base_dir = Path(args.dir)
    if not base_dir.exists():
        print(f"오류: 폴더를 찾을 수 없습니다 - {base_dir}")
        return

    txt_files = sorted([
        f for f in base_dir.glob("*.txt")
        if f.is_file() and f.name not in IGNORE_FILES
    ])

    if not txt_files:
        print("정리할 TXT 파일이 없습니다.")
        return

    print(f"총 {len(txt_files)}개의 파일을 분류합니다.\n")

    plan = {}
    for f in txt_files:
        category = classify(f.name)
        plan.setdefault(category, []).append(f)

    # 카테고리별 개수 미리보기
    for category in [c[0] for c in CATEGORIES] + [OTHER_FOLDER]:
        files = plan.get(category, [])
        if files:
            print(f"[{category}] {len(files)}개")
            for f in files:
                print(f"    - {f.name}")

    if args.dry_run:
        print("\n(--dry-run 모드이므로 실제 이동은 하지 않았습니다.)")
        return

    print("\n파일 이동을 시작합니다...")
    moved_count = 0
    skipped_count = 0

    for category, files in plan.items():
        target_dir = base_dir / category
        target_dir.mkdir(exist_ok=True)
        for f in files:
            dest = target_dir / f.name
            if dest.exists():
                print(f"  건너뜀 (이미 존재): {category}/{f.name}")
                skipped_count += 1
                continue
            shutil.move(str(f), str(dest))
            moved_count += 1

    print(f"\n완료: {moved_count}개 이동, {skipped_count}개 건너뜀")

    if plan.get(OTHER_FOLDER):
        print(f"\n'{OTHER_FOLDER}' 폴더로 분류된 파일은 키워드가 매칭되지 않은 항목입니다.")
        print("필요하시면 스크립트 상단의 CATEGORIES에 키워드를 추가해 재분류하실 수 있습니다.")


if __name__ == "__main__":
    main()

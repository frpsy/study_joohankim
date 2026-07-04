#!/bin/bash
# "[장자 길라잡이] NN - 제목.txt" -> "NN - 제목.txt" 로 변경
# subtitles 폴더 안에서 실행하세요.

for f in *.txt; do
    # "[장자 길라잡이] " 뒤에 오는 숫자와 나머지를 추출
    if [[ "$f" =~ ^\[장자\ 길라잡이\]\ ([0-9]+)\ (.*)$ ]]; then
        num="${BASH_REMATCH[1]}"
        rest="${BASH_REMATCH[2]}"
        newname="${num} - ${rest}"
        if [[ "$f" != "$newname" ]]; then
            echo "mv '$f' -> '$newname'"
            mv -- "$f" "$newname"
        fi
    fi
done
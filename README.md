# MuBoxing_AddUp

[앱 열기](https://nyk5473.github.io/MuBoxing_AddUp/)

## 오디오 분석 서버

GitHub Pages는 정적 파일만 게시합니다. `server/main.py`는 업로드한 오디오를 받아
FFmpeg로 디코딩하고, 파형의 에너지와 저·중·고역 분포를 측정하는 FastAPI 서버입니다.
업로드 파일은 메모리에서 처리하고 저장하지 않습니다. 최대 50MB, 분석 길이는 최대
10분입니다. 이 결과는 악기 분리, 보컬 감지, 코드 추정 또는 AI 모델의 판단이 아닙니다.
접근 가능한 공개 유튜브 영상은 STEP 2에서 링크를 붙여넣으면 서버가 오디오를 임시로
가져와 같은 방식으로 측정한 뒤 삭제합니다. 비공개·연령·지역 제한 영상이나 유튜브가
접근을 막은 영상은 분석할 수 없습니다. 분석 권한이 있는 영상에만 사용하세요.

### 로컬 실행

```bash
python -m pip install -r server/requirements.txt
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

`http://127.0.0.1:8000/`에서 앱과 서버가 함께 실행됩니다.
`/api/health`는 상태 확인, `/api/analyze`는 `file` 필드를 받는 multipart POST입니다.
`/api/analyze-youtube`는 `{"video_id":"영상 ID"}` JSON POST를 받습니다.

### 공개 배포

저장소의 `render.yaml`을 Render Blueprint로 배포하면 웹 서비스가 생성됩니다.
Render 계정에서 이 GitHub 저장소에 접근을 허용하고 서비스 생성까지 마쳐야 합니다.
현재 배포된 분석 서버는
[muboxing-addup-api.onrender.com](https://muboxing-addup-api.onrender.com/)입니다.
GitHub Pages 앱에는 이 주소가 기본값으로 설정됩니다. Render에 배포된 앱 주소로
직접 접속해도 같은 서버를 자동으로 사용합니다. 다른 주소로 재배포하면
GitHub Pages 앱의 **분석 서버 주소** 입력란에서 바꿀 수 있습니다.

무료 Render 인스턴스가 유휴 상태에서 재시작할 때 첫 요청이 지연될 수 있습니다.

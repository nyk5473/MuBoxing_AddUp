# MuBoxing_AddUp

[앱 열기](https://nyk5473.github.io/MuBoxing_AddUp/)

## 오디오 분석 서버

GitHub Pages는 정적 파일만 게시합니다. `server/main.py`는 업로드한 오디오를 받아
FFmpeg로 디코딩하고, 파형의 에너지와 저·중·고역 분포를 측정하는 FastAPI 서버입니다.
업로드 파일은 메모리에서 처리하고 저장하지 않습니다. 최대 50MB, 분석 길이는 최대
10분입니다. 이 결과는 악기 분리, 보컬 감지, 코드 추정 또는 AI 모델의 판단이 아닙니다.
유튜브 링크는 영상 열기에만 사용하며 링크의 오디오를 서버로 가져오지 않습니다.

### 로컬 실행

```bash
python -m pip install -r server/requirements.txt
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

`http://127.0.0.1:8000/`에서 앱과 서버가 함께 실행됩니다.
`/api/health`는 상태 확인, `/api/analyze`는 `file` 필드를 받는 multipart POST입니다.

### 공개 배포

저장소의 `render.yaml`을 Render Blueprint로 배포하면 웹 서비스가 생성됩니다.
Render 계정에서 이 GitHub 저장소에 접근을 허용하고 서비스 생성까지 마쳐야 합니다.
배포 후 받은 HTTPS 주소를 GitHub Pages 앱의 **분석 서버 주소**에 입력하면
브라우저에 저장되며 이후 업로드에 사용됩니다. Render에 배포된 앱 주소로
직접 접속하면 같은 서버를 자동으로 사용합니다.

서버를 GitHub Pages와 별도로 배포하지 않은 상태에서는 업로드 분석을 사용할 수 없습니다.

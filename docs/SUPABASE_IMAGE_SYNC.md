# Supabase 사진 자동 동기화 설정

`main` 브랜치의 `이미지/**`에 사진을 추가하거나 수정하면 GitHub Actions가 실행됩니다.

## GitHub Secrets

`resence` 저장소의 **Settings → Secrets and variables → Actions**에 아래 값을 추가합니다.

| Secret | 값 |
| --- | --- |
| `SUPABASE_URL` | Supabase 프로젝트 URL. 예: `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase의 `service_role` 키 |
| `SUPABASE_STORAGE_BUCKET` | 사진을 저장할 공개 Storage 버킷 이름 |

`SUPABASE_SERVICE_ROLE_KEY`는 절대 코드나 README에 작성하지 않습니다.

## 폴더와 DB 매핑

| GitHub 사진 폴더 | Supabase 테이블 | `member_name` |
| --- | --- | --- |
| `이미지/리브/` | `liv_images` | `LIV` |
| `이미지/메이/` | `mei_images` | `MEI` |
| `이미지/미나미/` | `minami_images` | `MINAMI` |
| `이미지/원이/` | `woni_images` | `WONI` |
| `이미지/제나/` | `jena_images` | `JENA` |

새로 추가한 사진은 Storage 업로드 후 해당 테이블에 `member_name`과 JSON 배열 형태의 `image_url`로 등록됩니다. 이미 등록된 URL은 다시 삽입하지 않습니다. 기존 사진 파일을 수정하면 같은 경로의 Storage 파일만 덮어씁니다.

`이미지/단체/` 사진은 Storage에는 업로드되지만 현재 앱의 멤버별 테이블과 연결되지 않으므로 DB에는 자동 등록하지 않습니다.

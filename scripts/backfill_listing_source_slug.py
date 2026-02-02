import os
from sqlalchemy import create_engine, text

# ✅ name -> slug 매핑(필요하면 여기만 늘리면 됨)
NAME_TO_SLUG = {
    "서울 바이닐": "seoulvinyl",
    "김밥레코즈": "gimbab",
    "스마트스토어": "smartstore",
    "예스24": "yes24",
    "알라딘": "aladin",
    "인스타그램": "instagram",
}

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL 환경변수가 필요합니다.")

    engine = create_engine(db_url)

    with engine.begin() as conn:
        # source_slug가 비어있는 row들만 가져오기
        rows = conn.execute(
            text("""
                SELECT id, source_name
                FROM listings
                WHERE source_slug IS NULL
            """)
        ).mappings().all()

        print(f"Backfill 대상: {len(rows)} rows")

        for r in rows:
            name = (r["source_name"] or "").strip()
            slug = NAME_TO_SLUG.get(name)

            # 매핑이 없으면 일부러 중단 (처음엔 이게 안전)
            if not slug:
                raise ValueError(f"slug 매핑 없음: '{name}' (listing.id={r['id']})")

            conn.execute(
                text("UPDATE listings SET source_slug = :slug WHERE id = :id"),
                {"slug": slug, "id": r["id"]},
            )

    print("✅ Backfill 완료")

if __name__ == "__main__":
    main()

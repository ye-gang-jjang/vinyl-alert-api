STORE_ICON_MAP = {
    "서울 바이닐": "/store-icons/seoulvinyl.png",
    "김밥레코즈": "/store-icons/gimbab.png",
    
    "스마트스토어": "/store-icons/smartstore.png",
    "예스24": "/store-icons/yes24.png",
    "알라딘": "/store-icons/aladin.png",
    
    "인스타그램": "/store-icons/instagram.png",
    "MPMG MUSIC": "/store-icons/mpmg.png",
    "KTOWN4U": "/store-icons/ktown4u.png",
    "핫트랙스(교보문고)": "/store-icons/hottracks.png",
}

def get_store_icon_url(store_name: str):
    if not store_name:
        return None
    return STORE_ICON_MAP.get(store_name.strip())

from PIL import Image, ImageOps
from pathlib import Path
from typing import List, Optional
from ..config import CROPS_DIR

def crop_objects_from_image(image_path: Path, scene_id: str, objects: list) -> list:
    """
    Crops detected 2D bounding boxes from the room image and saves them to storage/crops/.
    Returns updated objects list with crop_url.
    """
    if not image_path.exists():
        return objects

    try:
        with Image.open(image_path) as raw_img:
            # Auto-orient smartphone photos based on EXIF tag
            img = ImageOps.exif_transpose(raw_img)
            img_w, img_h = img.size

            for obj in objects:
                box_2d = getattr(obj, "box_2d", None) or (obj.get("box_2d") if isinstance(obj, dict) else None)
                if not box_2d or len(box_2d) != 4:
                    continue

                ymin, xmin, ymax, xmax = box_2d
                # Add slight padding (5%)
                pad_y = (ymax - ymin) * 0.05
                pad_x = (xmax - xmin) * 0.05

                left = max(0, int((xmin - pad_x) * img_w))
                top = max(0, int((ymin - pad_y) * img_h))
                right = min(img_w, int((xmax + pad_x) * img_w))
                bottom = min(img_h, int((ymax + pad_y) * img_h))

                if right > left and bottom > top:
                    cropped = img.crop((left, top, right, bottom))
                    obj_id = getattr(obj, "id", None) or obj.get("id")
                    crop_filename = f"{scene_id}_{obj_id}.jpg"
                    crop_path = CROPS_DIR / crop_filename
                    cropped.save(crop_path, "JPEG", quality=90)
                    
                    if isinstance(obj, dict):
                        obj["crop_url"] = f"/api/crops/{crop_filename}"
                    else:
                        setattr(obj, "crop_url", f"/api/crops/{crop_filename}")

    except Exception as e:
        print(f"Error cropping objects: {e}")

    return objects


# utils/update_pptx.py

from pptx import Presentation
# PresentationType 대신 Presentation을 직접 사용하거나, 타입을 더 명시적으로 지정
from pptx.util import Inches
from pptx.enum.shapes import MSO_SHAPE, MSO_AUTO_SIZE # MSO_AUTO_SIZE 임포트
from pptx.enum.text import MSO_ANCHOR, MSO_AUTOFIT, MSO_VERTICAL_ALIGNMENT, PP_ALIGN # PP_ALIGN 임포트

# Type hint를 위해 Presentation을 PresentationType으로 재정의할 필요 없이 직접 사용합니다.
# from pptx.presentation import Presentation as PresentationType

def load_template(template_path: str) -> Presentation:
    """
    지정된 경로에서 PPTX 템플릿을 로드합니다.
    """
    try:
        prs = Presentation(template_path)
        print(f"Loaded template from: {template_path}")
        return prs
    except Exception as e:
        print(f"Error loading PPT template {template_path}: {e}")
        raise


def edit_text_field(
    prs: Presentation,
    slide_index: int,
    new_text: str,
    is_title: bool = False,
    shape_name: str = None, # shape_name을 통한 접근 (PPTX 내부 이름)
    ph_index: int = None,    # placeholder_format.idx를 통한 접근 (PPTX 내부 인덱스)
    align_center: bool = True # 텍스트 중앙 정렬 여부
) -> Presentation:
    """
    주어진 슬라이드의 텍스트 필드를 수정합니다.
    `is_title=True`이면 슬라이드의 제목 Placeholder를 찾고,
    `shape_name`이 주어지면 해당 이름의 도형을,
    `ph_index`가 주어지면 해당 인덱스의 Placeholder를 찾습니다.
    텍스트 프레임을 찾지 못하면 경고를 출력합니다.
    """
    if slide_index >= len(prs.slides):
        print(f"Warning: Slide index {slide_index} out of bounds for editing.")
        return prs

    slide = prs.slides[slide_index]
    found_text_frame = False
    text_frame = None

    if is_title:
        if slide.shapes.title: # 제목 placeholder가 존재하는지 확인
            text_frame = slide.shapes.title.text_frame
        else:
            print(f"Warning: No title placeholder found on slide {slide_index} for title editing.")
    elif shape_name:
        for shape in slide.shapes:
            if shape.name == shape_name and shape.has_text_frame:
                text_frame = shape.text_frame
                break
        if not text_frame:
            print(f"Warning: No shape named '{shape_name}' with text frame found on slide {slide_index}.")
    elif ph_index is not None:
        for shape in slide.shapes.placeholders:
            if shape.has_text_frame and shape.placeholder_format.idx == ph_index:
                text_frame = shape.text_frame
                break
        if not text_frame:
            print(f"Warning: No placeholder with index {ph_index} and text frame found on slide {slide_index}.")
    else: # Fallback: is_title도 아니고, shape_name, ph_index도 없으면, 첫 번째 텍스트 프레임 찾기
        for shape in slide.shapes:
            if shape.has_text_frame:
                text_frame = shape.text_frame
                break
        if not text_frame:
            print(f"Warning: No generic text frame found on slide {slide_index} for editing.")
    
    if text_frame:
        text_frame.clear() # 기존 텍스트 모두 삭제
        p = text_frame.paragraphs[0] # 첫 번째 문단 가져오기
        run = p.add_run()
        run.text = new_text

        # 자동 크기 조정 (텍스트가 넘치면 셰이프 크기 조정)
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        
        # 텍스트 정렬 설정
        if align_center:
            p.alignment = PP_ALIGN.CENTER
        else:
            p.alignment = PP_ALIGN.LEFT # 기본은 왼쪽 정렬 (false일 때)

        found_text_frame = True
    
    if not found_text_frame:
        print(f"Warning: Failed to find or edit any suitable text field on slide {slide_index}. No text was inserted.")

    return prs


def _copy_slide_content(source_slide, new_slide):
    """
    원본 슬라이드의 모든 도형(텍스트, 이미지 등)을 새 슬라이드로 깊은 복사합니다.
    (python-pptx 템플릿 복제에서 가장 복잡한 부분 중 하나)
    """
    for shape in source_slide.shapes:
        if shape.has_text_frame:
            # 텍스트 프레임 복사
            left, top, width, height = shape.left, shape.top, shape.width, shape.height
            new_shape = new_slide.shapes.add_textbox(left, top, width, height)
            new_text_frame = new_shape.text_frame
            new_text_frame.text = shape.text_frame.text
            # 폰트, 크기, 색상 등 서식 복사는 별도의 복잡한 로직이 필요하며,
            # python-pptx의 제한된 API로 인해 모든 서식을 완벽하게 복제하기는 어렵습니다.
            # 여기서는 텍스트 내용만 복사하는 것으로 단순화합니다.
        elif shape.has_table:
            # 테이블 복사는 훨씬 더 복잡합니다. 여기서는 생략.
            pass
        elif shape.shape_type == MSO_SHAPE.PICTURE:
            # 이미지 복사 (원본 이미지 파일 경로가 필요할 수 있음)
            # 여기서는 이미지 파일 경로에 직접 접근하기 어려우므로 생략합니다.
            pass
        else:
            # 기타 도형 (도형 속성은 복잡)
            pass
    # 이 함수는 모든 도형을 완벽하게 복제하지 못할 수 있습니다.
    # 템플릿의 서식을 완벽히 유지하려면 PPT 템플릿 자체가 빈 placeholder만 포함하도록 설계하는 것이 좋습니다.


def add_slides_with_text(
    prs: Presentation,
    template_slide_index: int,
    texts_for_slides: list,
    is_title_field: bool = False, # 첫 번째 텍스트 필드를 제목으로 사용할지 여부
    target_ph_index: int = None,   # 텍스트를 채울 Placeholder 인덱스 (is_title이 False일 때)
    target_shape_name: str = None # 텍스트를 채울 Shape 이름 (is_title이 False일 때)
) -> dict:
    """
    주어진 텍스트 리스트만큼 슬라이드를 복제하고 텍스트를 채웁니다.
    첫 번째 텍스트는 `template_slide_index`의 원본 슬라이드에 채워지고,
    나머지는 복제된 슬라이드에 채워집니다.
    """
    added_slide_count = 0
    if not texts_for_slides:
        return {"prs": prs, "added_slide_count": 0}

    original_slide_template = prs.slides[template_slide_index]
    slide_layout = original_slide_template.slide_layout

    # 1. 첫 번째 텍스트는 원본 슬라이드에 채웁니다.
    edit_text_field(
        prs=prs,
        slide_index=template_slide_index,
        is_title=is_title_field,
        new_text=texts_for_slides[0],
        ph_index=target_ph_index,
        shape_name=target_shape_name
    )

    # 2. 나머지 텍스트들을 위한 슬라이드를 복제하고 텍스트를 채웁니다.
    for i in range(1, len(texts_for_slides)):
        # 새 슬라이드를 복제하고 콘텐츠 복사 (단순 복제)
        new_slide = prs.slides.add_slide(slide_layout) # 새 슬라이드 추가
        _copy_slide_content(original_slide_template, new_slide) # 원본 템플릿 슬라이드의 내용을 새 슬라이드로 복사

        # 새 슬라이드에 텍스트 채우기
        edit_text_field(
            prs=prs,
            slide_index=prs.slides.index(new_slide), # 새 슬라이드의 실제 인덱스
            is_title=is_title_field,
            new_text=texts_for_slides[i],
            ph_index=target_ph_index,
            shape_name=target_shape_name
        )
        added_slide_count += 1
    
    # 총 추가된 슬라이드 수는 첫 슬라이드를 제외한 복제된 슬라이드 수입니다.
    # 하지만 호출하는 쪽에서 인덱스 보정을 위해선 추가된 슬라이드 수를 정확히 알아야 합니다.
    # 만약 원본 슬라이드를 사용하지 않고 모두 복제된 슬라이드를 사용한다면,
    # added_slide_count는 len(texts_for_slides)가 될 것입니다.
    # 여기서는 "첫 번째 텍스트는 원본에 채우고 나머지를 추가"하는 방식이므로,
    # 첫 텍스트를 제외한 나머지 텍스트 수만큼 슬라이드가 추가됩니다.
    
    return {"prs": prs, "added_slide_count": added_slide_count}


# 기존 duplicate_and_add_slide -> add_slides_with_text로 통합/개선
# add_lyrics_slides 함수는 add_slides_with_text의 특정 사용 사례가 됩니다.
def add_lyrics_slides(prs: Presentation, duplicate_slide_index: int, slide_texts: list) -> dict:
    """
    찬양 가사 슬라이드를 추가합니다.
    `add_slides_with_text`를 사용하여 구현됩니다.
    """
    # 찬양 가사 슬라이드는 보통 제목 Placeholder가 아닌, 내용 Placeholder에 들어갑니다.
    # 템플릿의 가사 Placeholder 인덱스나 이름을 확인하고 아래 ph_index/shape_name을 설정하세요.
    # 예시: 템플릿의 가사 Placeholder가 index 1번 (제목 다음)에 있다면 ph_index=1 사용.
    # 템플릿의 가사 텍스트 상자 이름이 "LyricsPlaceholder"라면 shape_name="LyricsPlaceholder" 사용.
    # 여기서는 ph_index=1을 기본으로 가정합니다.
    return add_slides_with_text(prs, duplicate_slide_index, slide_texts, is_title_field=False, ph_index=1)


# 기존 add_ads_slides 함수 개선
def add_ads_slides(prs: Presentation, ads_list: list, template_slide_index: int) -> int:
    """
    광고 목록을 기반으로 슬라이드를 추가합니다.
    각 광고는 새 슬라이드에 제목과 내용이 들어갑니다.
    """
    if not ads_list:
        return 0

    added_count = 0
    original_ad_template_slide = prs.slides[template_slide_index]
    slide_layout = original_ad_template_slide.slide_layout

    for i, ad_data in enumerate(ads_list):
        current_slide_index = template_slide_index if i == 0 else prs.slides.index(prs.slides.add_slide(slide_layout))
        current_slide = prs.slides[current_slide_index]

        if i > 0: # 첫 번째 광고가 아니면 복사
            _copy_slide_content(original_ad_template_slide, current_slide)
            added_count += 1

        # 광고 제목 (is_title=True 또는 특정 Placeholder)
        edit_text_field(
            prs=prs,
            slide_index=current_slide_index,
            is_title=True, # 템플릿의 제목 Placeholder에 광고 제목
            new_text=ad_data.get("title", ""),
            align_center=False # 광고 제목은 보통 왼쪽 정렬
        )
        # 광고 내용 (is_title=False, 특정 Placeholder 또는 shape_name)
        edit_text_field(
            prs=prs,
            slide_index=current_slide_index,
            is_title=False,
            new_text=ad_data.get("contents", ""),
            ph_index=1 # 템플릿의 내용 Placeholder 인덱스 (가정)
            # 또는 shape_name="AdContentsPlaceholder"
        )
    return added_count


# 기존 add_bible_slides 함수 개선
def add_bible_slides(prs: Presentation, bible_contents_list: list, template_slide_index: int) -> int:
    """
    성경 구절 내용을 기반으로 슬라이드를 추가합니다.
    각 구절은 새 슬라이드에 제목(구절)과 내용이 들어갑니다.
    """
    if not bible_contents_list:
        return 0

    added_count = 0
    original_bible_template_slide = prs.slides[template_slide_index]
    slide_layout = original_bible_template_slide.slide_layout

    for i, bible_data in enumerate(bible_contents_list):
        current_slide_index = template_slide_index if i == 0 else prs.slides.index(prs.slides.add_slide(slide_layout))
        current_slide = prs.slides[current_slide_index]

        if i > 0: # 첫 번째 구절이 아니면 복사
            _copy_slide_content(original_bible_template_slide, current_slide)
            added_count += 1

        # 성경 구절 제목 (is_title=True 또는 특정 Placeholder)
        edit_text_field(
            prs=prs,
            slide_index=current_slide_index,
            is_title=True, # 템플릿의 제목 Placeholder에 성경 구절 (예: 요1:1)
            new_text=bible_data.get("title", ""),
        )
        # 성경 구절 내용 (is_title=False, 특정 Placeholder 또는 shape_name)
        edit_text_field(
            prs=prs,
            slide_index=current_slide_index,
            is_title=False,
            new_text=bible_data.get("contents", ""),
            ph_index=10 # 템플릿의 내용 Placeholder 인덱스 (가정, 원래 코드에서 10 사용)
            # 또는 shape_name="BibleContentsPlaceholder"
        )
    return added_count


def save_presentation(prs: Presentation, save_path: str):
    """
    프레젠테이션을 지정된 경로에 저장합니다.
    """
    try:
        prs.save(save_path)
        print(f"Presentation saved to: {save_path}")
    except Exception as e:
        print(f"Error saving presentation to {save_path}: {e}")
        raise
from tests.conftest import det
from visionai.vision.announcer import Announcer
from visionai.vision.detector import _clock, _position, _proximity, summarize


def say(announcer, objects, now):
    a = announcer.update(objects, now=now)
    return a.text if a else None


def test_position_thirds():
    assert _position(10, 300) == "left"
    assert _position(150, 300) == "ahead"
    assert _position(290, 300) == "right"


def test_proximity_by_frame_share():
    assert _proximity(30, 100) == "very close"
    assert _proximity(10, 100) == "close"
    assert _proximity(1, 100) == "far"


def test_summary_empty():
    assert "don't see" in summarize([])


def test_summary_nearest_first_with_plurals():
    objects = [
        det("chair", "left", "far", 5),
        det("chair", "left", "far", 6),
        det("person", "ahead", "very close", 50),
    ]
    assert summarize(objects) == "Person ahead, very close. 2 chairs on your left."


def test_summary_irregular_plural():
    assert summarize([det("person", "right"), det("person", "right")]) == "2 people on your right."


def test_announcer_respects_cooldown_and_repeat():
    a = Announcer(cooldown=4, repeat_after=20)
    chair = [det("chair", "left")]
    assert say(a, chair, 0) == "Chair on your left."
    assert say(a, chair, 2) is None  # cooldown
    assert say(a, chair, 10) is None  # already mentioned recently
    assert say(a, chair, 25) == "Chair on your left."  # reminder after repeat_after


def test_announcer_announces_new_objects():
    a = Announcer(cooldown=4, repeat_after=20)
    a.update([det("chair", "left")], now=0)
    assert say(a, [det("chair", "left"), det("dog", "right")], 5) == "Dog on your right."


def test_announcer_repeats_urgent_obstacles():
    a = Announcer(cooldown=4, repeat_after=20)
    close = [det("person", "ahead", "very close", 50)]
    first = a.update(close, now=0)
    assert first.text == "Careful. Person ahead, very close."
    assert first.urgent is True
    assert say(a, close, 5) == "Careful. Person ahead, very close."


# --- Clock-face directions -------------------------------------------------


def test_clock_mapping_spans_ten_to_two():
    assert [_clock(x, 500) for x in (0, 125, 250, 375, 500)] == [10, 11, 12, 1, 2]


def test_clock_style_summary_english():
    objects = [det("person", "ahead", "very close", 50), det("chair", "left", "far", 5)]
    objects[0].clock, objects[1].clock = 12, 10
    assert summarize(objects, style="clock") == "Person at 12 o'clock, very close. Chair at 10 o'clock."


# --- Other languages --------------------------------------------------------


def test_summary_in_hindi():
    objects = [det("person", "ahead", "very close", 50), det("chair", "left", "far", 5), det("chair", "left", "far", 6)]
    assert summarize(objects, lang="hi") == "व्यक्ति — सामने, बहुत पास। 2 कुर्सी — बाईं ओर।"


def test_summary_in_kannada_clock_style():
    d = det("dog", "right", "close", 20)
    d.clock = 2
    assert summarize([d], lang="kn", style="clock") == "ನಾಯಿ — 2 ಗಂಟೆಯ ದಿಕ್ಕಿನಲ್ಲಿ, ಹತ್ತಿರ."


def test_empty_summary_is_localized():
    assert summarize([], lang="ta") == "எனக்குத் தெரிந்த எந்தப் பொருளும் தென்படவில்லை."


def test_urgent_warning_is_localized():
    a = Announcer(lang="te")
    assert a.update([det("person", "ahead", "very close", 50)], now=0).text.startswith("జాగ్రత్త.")


def test_every_label_and_phrase_is_translated():
    from visionai import i18n
    from visionai.config import LANGUAGES

    assert set(i18n.LANG_ORDER) | {"en"} == set(LANGUAGES)
    assert len(i18n.LABELS) == 80  # all COCO classes YOLO can detect
    assert all(len(t) == len(i18n.LANG_ORDER) and all(t) for t in i18n.LABELS.values())
    keys = set(i18n.PHRASES["hi"])
    assert all(set(table) == keys for table in i18n.PHRASES.values())


def test_announcer_says_one_object_at_a_time_nearest_first():
    a = Announcer()
    objects = [det("chair", "left", "far", 5), det("dog", "right", "close", 30), det("cup", "ahead", "far", 4)]
    first = a.update(objects, now=0)
    assert first.text == "Dog on your right, close."
    assert first.clock == 2 and first.urgent is False
    assert say(a, objects, 5) == "Chair on your left."  # next most important, after the cooldown

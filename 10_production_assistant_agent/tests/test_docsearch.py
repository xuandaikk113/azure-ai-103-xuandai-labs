"""Test retrieval tài liệu nội bộ — thuần, không cần LLM."""

from assistant.tools.docsearch import search_docs


def test_search_ranks_relevant_doc(tmp_path):
    (tmp_path / "vpn.md").write_text("Hướng dẫn cài VPN và chọn gateway khu vực", encoding="utf-8")
    (tmp_path / "food.md").write_text("Thực đơn căng tin hôm nay có phở", encoding="utf-8")
    results = search_docs("làm sao cài vpn", str(tmp_path), top_k=1)
    assert results, "phải có kết quả khớp"
    assert results[0][0] == "vpn.md"


def test_no_match_returns_empty(tmp_path):
    (tmp_path / "a.md").write_text("xyz", encoding="utf-8")
    assert search_docs("zzz", str(tmp_path)) == []

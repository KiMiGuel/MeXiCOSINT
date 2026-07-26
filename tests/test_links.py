from mexicosint.main import generate_osint_links


def test_links_keep_wa_me_and_google_searches_only_for_social_sites():
    links = generate_osint_links("+526634647308")

    assert links["WhatsApp (wa.me)"] == "https://wa.me/526634647308"
    assert len([url for url in links.values() if "web.whatsapp.com" in url]) == 0
    assert len([url for url in links.values() if "/search/top/" in url]) == 0
    assert len([url for url in links.values() if "/search?q=" in url and "google.com" not in url]) == 0
    assert all("caller.com" not in url for url in links.values())
    assert "Google site:facebook.com" in links
    assert "Google site:tiktok.com" in links
    assert "Google site:x.com" in links
    assert "Google site:twitter.com" in links
    assert "%226634647308%22" in links["Google exact national"]

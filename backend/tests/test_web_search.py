from app.adapters import web_search


def test_clean_url_uddg():
    assert (
        web_search._clean_url("//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com")
        == "https://example.com"
    )


def test_clean_url_bing_redirect():
    href = (
        "https://www.bing.com/ck/a?!&amp;&amp;p=x"
        "&amp;u=a1aHR0cHM6Ly95b3Vjb250cm9sLmNvbS51YS8&amp;ntb=1"
    )
    assert web_search._clean_url(href) == "https://youcontrol.com.ua/"


def test_strip_html():
    assert web_search._strip("<b>Hello</b> world") == "Hello world"


def test_parse_ddg_extracts_results():
    html = (
        '<div class="result">'
        '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com">'
        "Example <b>Site</b></a>"
        '<a class="result__snippet">This is a snippet</a>'
        "</div>"
    )
    results = web_search.parse_ddg(html)
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com"
    assert results[0]["title"] == "Example Site"
    assert results[0]["snippet"] == "This is a snippet"


def test_parse_bing_extracts_results():
    html = (
        '<li class="b_algo">'
        '<h2><a href="https://example.com">Example</a></h2>'
        "<p>A snippet</p>"
        "</li>"
    )
    results = web_search.parse_bing(html)
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com"
    assert results[0]["title"] == "Example"
    assert results[0]["snippet"] == "A snippet"

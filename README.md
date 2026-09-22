# Task 3 - Playwright

Parser for brain.com.ua on Playwright: opens the main page, searches for
`Apple iPhone 15 128GB Black`, opens the first search result and collects the
product data; results are saved to PostgreSQL via Django ORM.

Run: `python modules/1_get_product_info.py`

## Project files

| File                              | Purpose                                                                 |
|-----------------------------------|-------------------------------------------------------------------------|
| `parser_app/models.py`            | `Product` model — one row per parsed product: text fields, `ArrayField` for image links, `JSONField` for the full characteristics dictionary, `search_query` and `link` as service fields |
| `modules/load_django.py`          | Bootstraps Django for standalone scripts (adds the project to `sys.path`, sets `DJANGO_SETTINGS_MODULE`, calls `django.setup()`) so `modules/*.py` can use the ORM |
| `modules/1_get_product_info.py`   | The parser: drives the browser through the search scenario, extracts the fields from the product page, prints them and saves them to the `Product` table |
| `results/parser_app_product.csv`  | CSV export of the `Product` table (pgAdmin)                             |
| `results/*.dump`                  | PostgreSQL dump of the database (pgAdmin, custom format)                |

The model is field-for-field identical to the Selenium version of this task, so
the CSV exports of the two projects can be compared row by row.

## Browser

The parser runs the real Chrome (`channel="chrome"`) in headless mode with
`--disable-blink-features=AutomationControlled` in `BROWSER_ARGS`, and a normal
Chrome `USER_AGENT`, `viewport`, `locale` and `timezone_id` in
`CONTEXT_OPTIONS`.

The site is behind Cloudflare, and three of those settings are required to get
past it: the Chrome channel, the flag and the user agent.

One browser instance is created in `launch_browser()`, used for the whole
scenario and closed in `finally`.

## Sync or async

`sync_playwright` is used: the task parses a single product on a single page
and the steps are strictly sequential, so async has nothing to overlap.

The ORM call is kept outside the `with sync_playwright()` block — inside it
Django raises `SynchronousOnlyOperation`.

## Scenario

| Step | Function            | Action                                                                   | Waits for                                    |
|------|---------------------|--------------------------------------------------------------------------|----------------------------------------------|
| 1    | `get_url`           | opens `https://brain.com.ua/`                                            | `div.header-bottom-in` (header with search)  |
| 2    | `search_product`    | types the query into `input.quick-search-input` with `press_sequentially` | the input is clickable                       |
| 3    | `search_product`    | clicks the "Знайти" button `input.qsr-submit` in the quick search overlay | the button is visible; then the first `div.br-pcg-product-wrapper` on the results page |
| 4    | `open_first_result` | scrolls to and clicks the title link of the first product card           | `div.br-pr-chr` on the product page          |
| 5    | `get_product_data`  | collects the fields (table below)                                        | —                                            |
| 6    | `pprint`            | prints the collected dictionary                                          | —                                            |
| 7    | `save_product`      | `Product.objects.get_or_create(**product)`                               | —                                            |

Every page transition is followed by a wait for a marker element of the new
page and a randomized `pause()` (1.5-3.5 s), so the page is never parsed before
it is rendered.

## How the parser works

Every element is located and verified manually in DevTools with XPath; the
parser uses short XPath expressions based on a class or a label text.

| Field                    | XPath                                                        |
|--------------------------|--------------------------------------------------------------|
| `title`                  | `//h1[@class='main-title']`                                  |
| `price` / `sale_price`   | `//div[contains(@class,'main-price-block')]` → `.//div[@class='br-pr-op']//span` (old), `.//div[@class='br-pr-np']//span` (current) |
| `images`                 | `//div[contains(@class,'br-image-links')]//a[@class='product-modal-button']/img` → `src` |
| `product_code`           | `//span[@class='br-pr-code-val']`                            |
| `reviews_count`          | `//a[contains(@class,'scroll-to-element') and contains(@class,'reviews-count')]/span` |
| `color`, `memory`, `manufacturer`, `screen_diagonal`, `screen_resolution` | `//div[@class='br-pr-chr']` → `.//span[text()='<label>']/following-sibling::span` (Ukrainian and Russian labels) |
| `characteristics`        | `.//div[@class='br-pr-chr-item']/div/div` rows → `label: value` dictionary |
| `search_query`, `link`   | the search query constant and `page.url`                     |

Containers (`main-price-block`, `br-pr-chr`) are found once and reused. Each
field is wrapped in its own `try/except PlaywrightTimeoutError`, so a missing
element does not stop the script — the field is set to `None`.

## Saving

`Product.objects.get_or_create(**product)` saves the collected values to the
`Product` table as they are, without any extra processing.

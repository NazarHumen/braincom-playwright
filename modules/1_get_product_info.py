"""
Playwright parser for brain.com.ua: opens the main page, searches for
"Apple iPhone 15 128GB Black", opens the first search result and collects
the product fields, the photo links and the full characteristics dictionary,
prints the result and saves it to the Product table.
"""

from pprint import pprint
from random import uniform
from time import sleep

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from load_django import *
from parser_app.models import *

MAIN_URL = 'https://brain.com.ua/'
SEARCH_QUERY = 'Apple iPhone 15 128GB Black'
WAIT_TIMEOUT = 15000
FIELD_TIMEOUT = 5000

USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36')
BROWSER_ARGS = ['--disable-blink-features=AutomationControlled']
CONTEXT_OPTIONS = {
    'user_agent': USER_AGENT,
    'viewport': {'width': 1400, 'height': 900},
    'locale': 'uk-UA',
    'timezone_id': 'Europe/Kyiv',
}


def pause(min_seconds=1.5, max_seconds=3.5):
    sleep(uniform(min_seconds, max_seconds))


def get_text(locator):
    return ' '.join(
        (locator.text_content(timeout=FIELD_TIMEOUT)).split())


def launch_browser(playwright):
    return playwright.chromium.launch(
        channel='chrome',
        headless=True,
        args=BROWSER_ARGS,
    )


def get_url(page, url):
    page.goto(url, timeout=WAIT_TIMEOUT * 2)
    page.wait_for_selector("xpath=//div[@class='header-bottom-in']",
                           timeout=WAIT_TIMEOUT)
    pause()


def search_product(page, query):
    search_input = page.locator(
        "xpath=//div[@class='header-bottom-in']"
        "//input[@class='quick-search-input']"
    )
    search_input.click(timeout=WAIT_TIMEOUT)
    search_input.press_sequentially(query, delay=60)

    search_button = page.locator("xpath=//input[@class='qsr-submit']")
    search_button.wait_for(state='visible', timeout=WAIT_TIMEOUT)
    search_button.click()

    page.wait_for_selector(
        "xpath=//div[contains(@class, 'br-pcg-product-wrapper')]",
        timeout=WAIT_TIMEOUT,
    )
    pause()


def open_first_result(page):
    first_result = page.locator(
        "xpath=(//div[contains(@class, 'br-pcg-product-wrapper')])[1]"
        "//div[contains(@class, 'br-pp-desc')]/a"
    )
    first_result.scroll_into_view_if_needed(timeout=WAIT_TIMEOUT)
    pause(0.5, 1.5)
    first_result.click()

    page.wait_for_selector("xpath=//div[@class='br-pr-chr']",
                           timeout=WAIT_TIMEOUT)
    pause()


def get_product_data(page):
    product = {}

    price_block = page.locator(
        "xpath=//div[contains(@class, 'main-price-block')]").first
    characteristics_block = page.locator(
        "xpath=//div[@class='br-pr-chr']").first

    try:
        product['title'] = get_text(
            page.locator("xpath=//h1[@class='main-title']")
        )
    except PlaywrightTimeoutError:
        product['title'] = None

    try:
        product['color'] = get_text(characteristics_block.locator(
            "xpath=.//span[text()='Колір' or text()='Цвет']"
            "/following-sibling::span"
        ))
    except PlaywrightTimeoutError:
        product['color'] = None

    try:
        product['memory'] = get_text(characteristics_block.locator(
            'xpath=.//span[text()="Вбудована пам\'ять" '
            'or text()="Встроенная память"]/following-sibling::span'
        ))
    except PlaywrightTimeoutError:
        product['memory'] = None

    try:
        product['manufacturer'] = get_text(characteristics_block.locator(
            "xpath=.//span[text()='Виробник' or text()='Производитель']"
            "/following-sibling::span"
        ))
    except PlaywrightTimeoutError:
        product['manufacturer'] = None

    try:
        current_price = get_text(
            price_block.locator("xpath=.//div[@class='br-pr-np']//span")
        )
        old_price = price_block.locator(
            "xpath=.//div[@class='br-pr-op']//span")
        if old_price.count():
            product['price'] = get_text(old_price)
            product['sale_price'] = current_price
        else:
            product['price'] = current_price
            product['sale_price'] = None
    except PlaywrightTimeoutError:
        product['price'] = None
        product['sale_price'] = None

    try:
        images = [
            image.get_attribute('src')
            for image in page.locator(
                "xpath=//div[contains(@class, 'br-image-links')]"
                "//a[@class='product-modal-button']/img"
            ).all()
        ]
        product['images'] = list(dict.fromkeys(images)) or None
    except PlaywrightTimeoutError:
        product['images'] = None

    try:
        product['product_code'] = get_text(
            page.locator("xpath=//span[@class='br-pr-code-val']").first
        )
    except PlaywrightTimeoutError:
        product['product_code'] = None

    try:
        product['reviews_count'] = int(get_text(
            page.locator(
                "xpath=//a[contains(@class, 'scroll-to-element') "
                "and contains(@class, 'reviews-count')]/span"
            ).first
        ))
    except (PlaywrightTimeoutError, ValueError):
        product['reviews_count'] = None

    try:
        product['screen_diagonal'] = get_text(characteristics_block.locator(
            "xpath=.//span[text()='Діагональ екрану' "
            "or text()='Диагональ экрана']/following-sibling::span"
        ))
    except PlaywrightTimeoutError:
        product['screen_diagonal'] = None

    try:
        product['screen_resolution'] = get_text(characteristics_block.locator(
            "xpath=.//span[text()='Роздільна здатність екрану' "
            "or text()='Разрешение экрана']/following-sibling::span"
        ))
    except PlaywrightTimeoutError:
        product['screen_resolution'] = None

    try:
        characteristics = {}
        for row in characteristics_block.locator(
                "xpath=.//div[@class='br-pr-chr-item']/div/div").all():
            label, value = row.locator('xpath=./span').all()
            characteristics[get_text(label)] = get_text(value)
        product['characteristics'] = characteristics or None
    except (PlaywrightTimeoutError, ValueError):
        product['characteristics'] = None

    product['search_query'] = SEARCH_QUERY
    product['link'] = page.url

    return product


def save_product(product):
    Product.objects.get_or_create(**product)


if __name__ == '__main__':
    product = None

    with sync_playwright() as playwright:
        browser = launch_browser(playwright)

        try:
            page = browser.new_context(**CONTEXT_OPTIONS).new_page()
            get_url(page, MAIN_URL)
            search_product(page, SEARCH_QUERY)
            open_first_result(page)
            product = get_product_data(page)
        except PlaywrightTimeoutError as error:
            print(f'Page element did not load in time: {error.message}')
        finally:
            browser.close()

    if product:
        pprint(product, sort_dicts=False)
        save_product(product)

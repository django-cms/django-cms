def get_response_headers(response):
    if hasattr(response, '_headers'):
        response_headers = response._headers
    else:
        response_headers = response.headers
    return response_headers
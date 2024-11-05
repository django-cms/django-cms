def get_response_headers(response):
    """
    Django 3.2+ comes with changes to the response headers and the _headers is not present
    in the newer versions. So this method checks if it's present in the response or not, else
    returns the newer attribute headers from the response.
    """
    if hasattr(response, '_headers'):
        response_headers = response._headers
    else:
        response_headers = response.headers
    return response_headers

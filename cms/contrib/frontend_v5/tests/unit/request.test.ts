import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { del, get, getCookie, post, put, request, RequestError } from '../../frontend/modules/request';

/**
 * Build a Response-shaped mock without depending on the real Response
 * constructor (jsdom's varies). We control exactly what fetch returns.
 */
function mockResponse(opts: {
    status?: number;
    statusText?: string;
    contentType?: string;
    body?: string;
}): Response {
    const status = opts.status ?? 200;
    const headers = new Headers();
    if (opts.contentType) headers.set('Content-Type', opts.contentType);
    return {
        ok: status >= 200 && status < 300,
        status,
        statusText: opts.statusText ?? '',
        headers,
        json: async () => JSON.parse(opts.body ?? 'null'),
        text: async () => opts.body ?? '',
    } as unknown as Response;
}

describe('getCookie', () => {
    afterEach(() => {
        // Clear all cookies between tests by overwriting with expired dates.
        for (const cookie of document.cookie.split(';')) {
            const eq = cookie.indexOf('=');
            const name = (eq > -1 ? cookie.substring(0, eq) : cookie).trim();
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
        }
    });

    it('returns null when the cookie is not set', () => {
        expect(getCookie('nonexistent')).toBeNull();
    });

    it('reads a simple cookie value', () => {
        document.cookie = 'csrftoken=abc123';
        expect(getCookie('csrftoken')).toBe('abc123');
    });

    it('decodes URL-encoded values', () => {
        document.cookie = `weird=${encodeURIComponent('a/b c+d')}`;
        expect(getCookie('weird')).toBe('a/b c+d');
    });

    it('handles multiple cookies and finds the right one', () => {
        document.cookie = 'first=one';
        document.cookie = 'csrftoken=xyz';
        document.cookie = 'last=tail';
        expect(getCookie('csrftoken')).toBe('xyz');
        expect(getCookie('first')).toBe('one');
        expect(getCookie('last')).toBe('tail');
    });
});

describe('request', () => {
    let fetchMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);
        // Clear cookies so cross-test contamination can't sneak a CSRF token in.
        for (const cookie of document.cookie.split(';')) {
            const eq = cookie.indexOf('=');
            const name = (eq > -1 ? cookie.substring(0, eq) : cookie).trim();
            document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
        }
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    describe('success paths', () => {
        it('GET parses a JSON response', async () => {
            fetchMock.mockResolvedValueOnce(
                mockResponse({ contentType: 'application/json', body: '{"hello":"world"}' }),
            );
            const result = await get<{ hello: string }>('/api/');
            expect(result).toEqual({ hello: 'world' });
            expect(fetchMock).toHaveBeenCalledTimes(1);
            const [url, init] = fetchMock.mock.calls[0]!;
            expect(url).toBe('/api/');
            expect(init.method).toBe('GET');
            expect(init.credentials).toBe('same-origin');
        });

        it('GET returns text for non-JSON responses', async () => {
            fetchMock.mockResolvedValueOnce(
                mockResponse({ contentType: 'text/plain', body: 'just text' }),
            );
            const result = await get<string>('/api/');
            expect(result).toBe('just text');
        });

        it('GET handles 204 No Content as null', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ status: 204 }));
            const result = await get('/api/');
            expect(result).toBeNull();
        });

        it('returns null for malformed JSON instead of crashing', async () => {
            fetchMock.mockResolvedValueOnce(
                mockResponse({ contentType: 'application/json', body: 'not-json' }),
            );
            const result = await get('/api/');
            expect(result).toBeNull();
        });

        it('POST sends an object body as JSON with correct Content-Type', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            await post('/api/', { name: 'thing' });
            const init = fetchMock.mock.calls[0]![1];
            expect(init.method).toBe('POST');
            expect(init.body).toBe('{"name":"thing"}');
            expect(init.headers['Content-Type']).toBe('application/json');
        });

        it('POST passes FormData through and does NOT set Content-Type', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            const fd = new FormData();
            fd.append('field', 'value');
            await post('/api/', fd);
            const init = fetchMock.mock.calls[0]![1];
            expect(init.body).toBe(fd);
            // Browser sets multipart Content-Type with boundary itself —
            // we must NOT override it.
            expect(init.headers['Content-Type']).toBeUndefined();
        });

        it('POST passes URLSearchParams through unchanged', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            const params = new URLSearchParams({ a: '1', b: '2' });
            await post('/api/', params);
            const init = fetchMock.mock.calls[0]![1];
            expect(init.body).toBe(params);
            expect(init.headers['Content-Type']).toBeUndefined();
        });

        it('POST passes string bodies through unchanged', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            await post('/api/', 'raw=string');
            const init = fetchMock.mock.calls[0]![1];
            expect(init.body).toBe('raw=string');
        });

        it('omits the body entirely when none is given', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ status: 204 }));
            await get('/api/');
            const init = fetchMock.mock.calls[0]![1];
            expect(init.body).toBeUndefined();
        });

        it('always sends Accept: application/json', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            await get('/api/');
            const init = fetchMock.mock.calls[0]![1];
            expect(init.headers.Accept).toBe('application/json');
        });

        it('merges caller-provided headers', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            await get('/api/', { headers: { 'X-Custom': 'yes' } });
            const init = fetchMock.mock.calls[0]![1];
            expect(init.headers['X-Custom']).toBe('yes');
            expect(init.headers.Accept).toBe('application/json');
        });

        it('forwards an AbortSignal to fetch', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ status: 204 }));
            const ctrl = new AbortController();
            await get('/api/', { signal: ctrl.signal });
            const init = fetchMock.mock.calls[0]![1];
            expect(init.signal).toBe(ctrl.signal);
        });
    });

    describe('CSRF', () => {
        it('adds X-CSRFToken to POST when csrftoken cookie exists', async () => {
            document.cookie = 'csrftoken=secret123';
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            await post('/api/', { x: 1 });
            const init = fetchMock.mock.calls[0]![1];
            expect(init.headers['X-CSRFToken']).toBe('secret123');
        });

        it('does NOT add X-CSRFToken to GET (safe method)', async () => {
            document.cookie = 'csrftoken=secret123';
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            await get('/api/');
            const init = fetchMock.mock.calls[0]![1];
            expect(init.headers['X-CSRFToken']).toBeUndefined();
        });

        it('does not add X-CSRFToken when no cookie is set', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            await post('/api/', {});
            const init = fetchMock.mock.calls[0]![1];
            expect(init.headers['X-CSRFToken']).toBeUndefined();
        });

        it('honors a custom csrfCookieName', async () => {
            document.cookie = 'mytoken=abc';
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            await post('/api/', {}, { csrfCookieName: 'mytoken' });
            const init = fetchMock.mock.calls[0]![1];
            expect(init.headers['X-CSRFToken']).toBe('abc');
        });

        it('does not overwrite a caller-provided X-CSRFToken header', async () => {
            document.cookie = 'csrftoken=cookie-value';
            fetchMock.mockResolvedValueOnce(mockResponse({ contentType: 'application/json', body: '{}' }));
            await post('/api/', {}, { headers: { 'X-CSRFToken': 'caller-value' } });
            const init = fetchMock.mock.calls[0]![1];
            expect(init.headers['X-CSRFToken']).toBe('caller-value');
        });

        it('adds X-CSRFToken to PUT and DELETE', async () => {
            document.cookie = 'csrftoken=tk';
            fetchMock.mockResolvedValue(mockResponse({ status: 204 }));
            await put('/api/1/', { x: 1 });
            await del('/api/1/');
            expect(fetchMock.mock.calls[0]![1].headers['X-CSRFToken']).toBe('tk');
            expect(fetchMock.mock.calls[1]![1].headers['X-CSRFToken']).toBe('tk');
        });
    });

    describe('error paths', () => {
        it('throws RequestError for 4xx with parsed JSON body', async () => {
            fetchMock.mockResolvedValueOnce(
                mockResponse({
                    status: 400,
                    statusText: 'Bad Request',
                    contentType: 'application/json',
                    body: '{"error":"missing field"}',
                }),
            );
            await expect(post('/api/', {})).rejects.toMatchObject({
                name: 'RequestError',
                status: 400,
                statusText: 'Bad Request',
                url: '/api/',
                body: { error: 'missing field' },
            });
        });

        it('throws RequestError for 5xx with text body', async () => {
            fetchMock.mockResolvedValueOnce(
                mockResponse({
                    status: 500,
                    statusText: 'Internal Server Error',
                    contentType: 'text/html',
                    body: '<h1>boom</h1>',
                }),
            );
            const err = await get('/api/').catch((e) => e as unknown);
            expect(err).toBeInstanceOf(RequestError);
            const reqErr = err as RequestError;
            expect(reqErr.status).toBe(500);
            expect(reqErr.body).toBe('<h1>boom</h1>');
            expect(reqErr.message).toContain('500');
        });

        it('throws RequestError for 401 even with no body', async () => {
            fetchMock.mockResolvedValueOnce(
                mockResponse({ status: 401, statusText: 'Unauthorized' }),
            );
            await expect(get('/api/')).rejects.toMatchObject({
                status: 401,
                statusText: 'Unauthorized',
            });
        });
    });

    describe('method shortcuts', () => {
        it('request() called directly works for arbitrary methods', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ status: 204 }));
            await request('PATCH', '/api/');
            expect(fetchMock.mock.calls[0]![1].method).toBe('PATCH');
        });

        it('lowercase method gets uppercased', async () => {
            fetchMock.mockResolvedValueOnce(mockResponse({ status: 204 }));
            await request('post', '/api/');
            expect(fetchMock.mock.calls[0]![1].method).toBe('POST');
        });
    });
});

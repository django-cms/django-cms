(function() {
    'use strict';

    // DOMContentLoaded event handler
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    function init() {
        // INFO: it is not possible to put a form inside a form, so
        // the actions have to create their own form on click.
        // Note for any apps inheriting the burger menu, this will also capture those events.

        function closeSideFrame() {
            try {
                window.top.CMS.API.Sideframe.close();
            } catch {}
        }

        // Add click handlers for actions
        document.querySelectorAll('.js-action, .cms-js-edit-btn, .cms-actions-dropdown-menu-item-anchor')
            .forEach(function(element) {
                element.addEventListener('click', function(e) {
                    let action = e.currentTarget;
                    let classList = action.getAttribute('class') || '';
                    let formMethod = classList.indexOf('cms-form-post-method') !== -1 ? 'POST' : 'GET';
                    let keepSideFrame = classList.indexOf('js-keep-sideframe') !== -1;

                    if (formMethod === 'GET') {
                        if (!keepSideFrame) {
                            action.setAttribute('target', '_top');
                            closeSideFrame();
                        }
                    } else {
                        e.preventDefault();
                        /* Get csrftoken either from form (admin) or from the toolbar */
                        let formToken = document.querySelector('form input[name="csrfmiddlewaretoken"]');
                        let csrfTokenValue = (formToken ? formToken.value : formToken) || window.CMS.config.csrf;

                        let fakeForm = document.createElement('form');
                        fakeForm.style.display = 'none';
                        fakeForm.setAttribute('action', action.getAttribute('href'));
                        fakeForm.setAttribute('method', formMethod);

                        let csrfInput = document.createElement('input');
                        csrfInput.type = 'hidden';
                        csrfInput.name = 'csrfmiddlewaretoken';
                        csrfInput.value = csrfTokenValue;
                        fakeForm.appendChild(csrfInput);

                        let body = window.top.document.body;

                        if (keepSideFrame) {
                            body = window.document.body;
                        } else {
                            closeSideFrame();
                        }
                        body.appendChild(fakeForm);
                        fakeForm.submit();
                    }
                });
            });

        // Close sideframe handler
        document.querySelectorAll('.js-close-sideframe').forEach(function(element) {
            element.addEventListener('click', function() {
                try {
                    window.top.CMS.API.Sideframe.close();
                } catch {}
            });
        });
    }

    // Hide django messages after timeout occurs to prevent content overlap
    // Targeting first item returned (there's only ever one messagelist per template):
    let messageList = document.getElementsByClassName('messagelist')[0];

    if (messageList !== undefined) {
        for (let item of messageList.children) {
            item.style.opacity = 1;
            setTimeout(() => {
                let fader = setInterval(() => {
                    item.style.opacity -= 0.05;
                    if (item.style.opacity < 0) {
                        item.style.display = 'none';
                        clearInterval(fader);
                    }
                }, 20);
            }, 5000);
        }
    }

    // Create burger menu:
    let createBurgerMenu = function createBurgerMenu(row) {
        // Find children with class 'field-list_actions'
        let actions = Array.from(row.children).filter(child =>
            child.classList.contains('field-list_actions')
        );

        if (!actions.length) {
            /* skip any rows without actions to avoid errors */
            return;
        }

        /* create burger menu anchor icon */
        let anchor = document.createElement('a');
        let icon = document.createElement('span');

        icon.setAttribute('class', 'cms-icon cms-icon-menu');
        anchor.setAttribute('class', 'btn cms-action-btn cms-burger-menu closed');
        anchor.setAttribute('title', 'Actions');
        anchor.appendChild(icon);

        /* create options container */
        let optionsContainer = document.createElement('div');
        let ul = document.createElement('ul');

        /* 'cms-actions-dropdown-menu' class is the main selector for the menu,
        'cms-actions-dropdown-menu-arrow-right-top' keeps the menu arrow in position. */
        optionsContainer.setAttribute(
            'class',
            'cms-actions-dropdown-menu cms-actions-dropdown-menu-arrow-right-top');
        ul.setAttribute('class', 'cms-actions-dropdown-menu-inner');

        /* get the existing actions and move them into the options container */
        let burgerActionButtons = Array.from(actions[0].children).filter(child =>
            child.classList.contains('cms-burger-action-btn')
        );

        burgerActionButtons.forEach(function(item) {
            let li = document.createElement('li');
            /* create an anchor from the item */
            let li_anchor = document.createElement('a');

            li_anchor.setAttribute('class', 'cms-actions-dropdown-menu-item-anchor');
            li_anchor.setAttribute('href', item.getAttribute('href'));

            if (item.classList.contains('cms-form-get-method')) {
                li_anchor.classList.add('cms-form-get-method'); // Ensure the fake-form selector is propagated to the new anchor
            }
            /* move the icon */
            if (item.children[0]) {
                li_anchor.appendChild(item.children[0]);
            }

            /* create the button text and construct the button */
            let span = document.createElement('span');

            span.setAttribute('class', 'label');
            span.appendChild(
                document.createTextNode(item.title)
            );

            li_anchor.appendChild(span);
            li.appendChild(li_anchor);
            ul.appendChild(li);

            /* destroy original replaced buttons */
            actions[0].removeChild(item);
        });

        if (ul.children.length > 0) {
            /* add the options to the drop-down */
            optionsContainer.appendChild(ul);
            actions[0].appendChild(anchor);
            document.body.appendChild(optionsContainer);

            /* listen for burger menu clicks */
            anchor.addEventListener('click', function (ev) {
                ev.stopPropagation();
                toggleBurgerMenu(anchor, optionsContainer);
            });

            /* close burger menu if clicking outside */
            window.addEventListener('click', function () {
                closeBurgerMenu();
            });
        }
    };

    let toggleBurgerMenu = function toggleBurgerMenu(burgerMenuAnchor, optionsContainer) {
        let closed = burgerMenuAnchor.classList.contains('closed');

        closeBurgerMenu();

        if (closed) {
            burgerMenuAnchor.classList.remove('closed');
            burgerMenuAnchor.classList.add('open');
            optionsContainer.classList.remove('closed');
            optionsContainer.classList.add('open');
        } else {
            burgerMenuAnchor.classList.add('closed');
            burgerMenuAnchor.classList.remove('open');
            optionsContainer.classList.add('closed');
            optionsContainer.classList.remove('open');
        }

        let rect = burgerMenuAnchor.getBoundingClientRect();
        let scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        optionsContainer.style.left = (rect.left + scrollLeft - optionsContainer.offsetWidth - 5) + 'px';
        optionsContainer.style.top = (rect.top + scrollTop - 2) + 'px';
    };

    let closeBurgerMenu = function closeBurgerMenu() {
        document.querySelectorAll('.cms-actions-dropdown-menu').forEach(function(el) {
            el.classList.remove('open');
            el.classList.add('closed');
        });
        document.querySelectorAll('.cms-action-btn').forEach(function(el) {
            el.classList.remove('open');
            el.classList.add('closed');
        });
    };

    let resultList = document.getElementById('result_list');
    if (resultList) {
        resultList.querySelectorAll('tr').forEach(function(row) {
            createBurgerMenu(row);
        });
    }
})();

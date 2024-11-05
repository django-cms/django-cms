(function($) {
    $(function() {
        // INFO: it is not possible to put a form inside a form, so
        // the actions have to create their own form on click.
        // Note for any apps inheriting the burger menu, this will also capture those events.

        function closeSideFrame() {
            try {
                window.top.CMS.API.Sideframe.close();
            } catch (err) {}
        }
        $(`.js-action,
           .cms-js-edit-btn,
           .cms-actions-dropdown-menu-item-anchor`)
            .on('click', function(e) {
                let action = $(e.currentTarget);
                let formMethod = action.attr('class').indexOf('cms-form-post-method') !== -1 ? 'POST': 'GET';
                let keepSideFrame = action.attr('class').indexOf('js-keep-sideframe') !== -1;

                if (formMethod === 'GET') {
                    if (!keepSideFrame) {
                        action.attr('target', '_top');
                        closeSideFrame();
                    }
                } else {
                    e.preventDefault();
                    /* Get csrftoken either from form (admin) or from the toolbar */
                    let formToken = document.querySelector('form input[name="csrfmiddlewaretoken"]');
                    let csrfToken = '<input type="hidden" name="csrfmiddlewaretoken" value="' +
                        ((formToken ? formToken.value : formToken) || window.CMS.config.csrf) + '">';
                    let fakeForm = $(
                        '<form style="display: none" action="' + action.attr('href') + '" method="' +
                               formMethod + '">' + csrfToken +
                        '</form>'
                    );
                    let body = window.top.document.body;
                    if (keepSideFrame) {
                        body = window.document.body;
                    } else {
                        closeSideFrame();
                    }
                    fakeForm.appendTo(body).submit();
                }
            });

        $('.js-close-sideframe').on('click', function () {
            try {
                window.top.CMS.API.Sideframe.close();
            } catch (e) {}
        });
    });

    // Hide django messages after timeout occurs to prevent content overlap
    $('document').ready(function(){
        // Targeting first item returned (there's only ever one messagelist per template):
        let messageList = document.getElementsByClassName("messagelist")[0];
        if (messageList !== undefined){
          for(let item of messageList.children){
            item.style.opacity = 1;
            setTimeout(() => {
              let fader = setInterval(() => {
                item.style.opacity -= 0.05;
                  if(item.style.opacity < 0) {
                    item.style.display = "none";
                    clearInterval(fader);
                  }
              }, 20);
            }, 5000);
          }
        }
    });

    // Create burger menu:
    $(function() {
         let createBurgerMenu = function createBurgerMenu(row) {

            let actions = $(row).children('.field-list_actions');
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
            $(actions[0]).children('.cms-burger-action-btn').each(function (index, item) {
              let li = document.createElement('li');
              /* create an anchor from the item */
              let li_anchor = document.createElement('a');
              li_anchor.setAttribute('class', 'cms-actions-dropdown-menu-item-anchor');
              li_anchor.setAttribute('href', $(item).attr('href'));

              if ($(item).hasClass('cms-form-get-method')) {
                li_anchor.classList.add('cms-form-get-method'); // Ensure the fake-form selector is propagated to the new anchor
              }
              /* move the icon */
              li_anchor.appendChild($(item).children()[0]);

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

            if ($(ul).children().length > 0) {
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
              $(window).click(function () {
                closeBurgerMenu();
              });
            }
          };

        let toggleBurgerMenu = function toggleBurgerMenu(burgerMenuAnchor, optionsContainer) {
            let bm = $(burgerMenuAnchor);
            let op = $(optionsContainer);
            let closed = bm.hasClass('closed');
            closeBurgerMenu();

            if (closed) {
              bm.removeClass('closed').addClass('open');
              op.removeClass('closed').addClass('open');
            } else {
              bm.addClass('closed').removeClass('open');
              op.addClass('closed').removeClass('open');
            }

            let pos = bm.offset();
            op.css('left', pos.left - op.width() - 5);
            op.css('top', pos.top - 2);
          };

        let closeBurgerMenu = function closeBurgerMenu() {
            $('.cms-actions-dropdown-menu').removeClass('open');
            $('.cms-actions-dropdown-menu').addClass('closed');
            $('.cms-action-btn').removeClass('open');
            $('.cms-action-btn').addClass('closed');
        };

        $('#result_list').find('tr').each(function (index, item) {
            createBurgerMenu(item);
        });

    });

})((typeof django !== 'undefined' && django.jQuery) || (typeof CMS !== 'undefined' && CMS.$) || false);

import $ from 'jquery';
import 'waypoints/lib/noframework.waypoints'; // waypoints don't expose main in package.json
import { once } from 'lodash';
import Velocity from 'velocity-animate';
import 'velocity-ui-pack';

export function initWaypoints(selector = '.js-waypoint') {
    $(selector).each((i, el) => {
        const element = $(el);
        const data = element.data('waypoint');
        const staggered = element.find('.js-stagger').toArray();

        new window.Waypoint({
            element: el,
            handler: once(() => {
                new Velocity([el, ...staggered], data.animation, {
                    duration: 400,
                    delay: 200,
                    stagger: 200,
                });
            }),
            ...data,
        });
    });
}

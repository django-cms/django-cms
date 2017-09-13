import $ from 'jquery';
import { initCopyFromContent } from './copy';
import { overridePlugin } from './plugin';
import { overrideStructureBoard } from './structureboard';

overridePlugin();
overrideStructureBoard();

$(() => {
    initCopyFromContent();
});

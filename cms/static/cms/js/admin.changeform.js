// Define the global CMS namespace, e.g. for widgets
const CMS = {
    API: {
    }
};

// expose to browser
if (typeof window !== 'undefined') {
    window.CMS = window.CMS || CMS;
}

import './modules/cms.changeform';

export default CMS;

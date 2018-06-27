import privacyManagement from 'addons/privacy-management';

window.analyticsIntegrations = null;

if (!privacyManagement.getPreference('STATISTICS')) {
    window.analyticsIntegrations = {
        integrations: {
            'Segment.io': false,
            'Google Analytics': false,
        },
    };
}

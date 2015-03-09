# -*- coding: utf-8 -*-
import locale
import gettext
import os

current_locale = 'en_US'
locale_dir = '/opt/ibm/zkvm-installer/po/'


class getTranslation:
    """
    Translation class
    """

    def __init__(self, domain):
        """
        Constructor

        @type  domain: basestring
        @param domain: translation domain
        """
        self.domain = domain

        # set default language
        self.current_locale = 'en_US'
    # __init__()

    def __call__(self, string):
        """
        Make the translation

        @type  string: basestring
        @param string: text to be translated
        """
        global locale_dir

        return getCustomString(string, self.domain, locale_dir)
    # __call__()

    def setLanguage(self, locale):
        """
        Set the current_locale

        @type  string: basestring
        @param string: locale paramete
        """
        global current_locale

        current_locale = locale
    # setLanguage()

_ = getTranslation('zKVM')


class getCustomString:

    def __init__(self, string, domain, localeDir):
        self.string = string
        self.domain = domain
        self.localeDir = localeDir
    # __init__()

    def localize(self):
        global current_locale
        language = gettext.translation(self.domain, self.localeDir, languages=[current_locale])
        language.install()

        return language.ugettext(self.string).encode('utf-8')
    # localize()

# getCustomString


def choose_language(viewer):
    """
    Displays the language screen to the user and sets the
    installer interface to that language

    @type  viewer: viewer
    @param viewer: interface object

    @rtype: basestr
    @returns: language selected
    """
    global _
    global locale_dir

    language_label = {
        'pt_BR': u'Português(BR)'.encode('utf-8'),
        'zh_CN': u'中国传统'.encode('utf-8'),
        'zh_TW': u'简化中国'.encode('utf-8'),
        'fr_FR': u'Français'.encode('utf-8'),
        'de_DE': u'Deutsch'.encode('utf-8'),
        'it_IT': u'Italiano'.encode('utf-8'),
        'Ja_JP': u'日本の'.encode('utf-8'),
        'ko_KR': u'한국의'.encode('utf-8'),
        'ru_RU': u'Русский'.encode('utf-8'),
        'es_ES': u'Español'.encode('utf-8'),
        }

    license_language_label = {
        'cs': u'Czech'.encode('utf-8'),
        'el': u'Greek'.encode('utf-8'),
        'in': u'Indonesian'.encode('utf-8'),
        'lt': u'Lithuanian'.encode('utf-8'),
        'sl': u'Slovenian'.encode('utf-8'),
        'pl': u'Polish'.encode('utf-8'),
        'tr': u'Turkish'.encode('utf-8'),
        }

    # options to be configured on menu screen
    menuOptions = []

    # rescue option
    directory_list = os.listdir(locale_dir)
    directory_list.sort()

    menuOptions.append(('English', 'en_US'))
#    for i in directory_list:
#        if os.path.exists(locale_dir + i + '/LC_MESSAGES/powerKVM.mo'):
#            if i != 'en_US' and i != 'ja_JP':
#                if i in language_label:
#                    menuOptions.append((language_label[i], i))
#                else:
#                    menuOptions.append((i, i))

    # hack to handle the languages only available for license
    #for lang, name in license_language_label.iteritems():
    #    menuOptions.append((name, lang))

    # get menu screen instance
    menuScreen = viewer.getChooseLanguage()

    # configure menu options
    menuScreen.setMenuOptions(menuOptions)

    # run menu screen and get the user option
    current_locale = menuScreen.run()

    # use english as default when user selected language
    # only available for the license text
    if len(current_locale) == 2:
        _.setLanguage('en_US')

    else:
        _.setLanguage(current_locale)

    return current_locale
# choose_language()


def setLanguageKS(lang):
    """
    Set the installer interface to the given language.

    @type  lang: str
    @param lang: language to be set

    @rtype: str
    @returns: language effectively set
    """
    global _

    availableLangs = [
        'pt_BR',
        'zh_CN',
        'zh_TW',
        'fr_FR',
        'de_DE',
        'it_IT',
        'Ja_JP',
        'ko_KR',
        'ru_RU',
        'es_ES',
        'en_US',
    ]

    if lang in availableLangs:
        current_locale = lang
    else:
        current_locale = 'en_US'
    _.setLanguage(current_locale)

    return current_locale
# setLanguageKS()

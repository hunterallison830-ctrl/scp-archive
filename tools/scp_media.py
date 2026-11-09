"""Sourced card image for each of the 36 anomalies, with its attribution.

Every entry points to a file downloaded into the private research cache. The
credit fields copy the source page's license box or the Wikimedia Commons file
metadata. `basis` records how the license was established:
  license-box  - per-file entry in the hosting wiki page's license box
  commons      - Wikimedia Commons file page metadata
  page-license - hosted on an SCP Wiki page whose citation box / footer states
                 CC BY-SA 3.0, with the artist named on that page but no
                 per-file license-box entry (weaker; flagged in credits)
"""
W = 'https://scp-wiki.wikidot.com/'
BYSA3 = ('CC BY-SA 3.0', 'https://creativecommons.org/licenses/by-sa/3.0/')
BY3 = ('CC BY 3.0', 'https://creativecommons.org/licenses/by/3.0/')
UTON = dict(author='Uton 2008', page=W + 'uton-game-postcard-artworks', basis='license-box', lic=BYSA3,
            note='Hand-drawn postcard fan art. The page lists each file with author Uton 2008 and CC BY-SA 3.0; the drawn label identifies the SCP.')

def art(file, title, author, page, url, basis='license-box', lic=BYSA3, note='', fit='cover', pos='50% 50%'):
    return dict(file=file, title=title, author=author, page=page, url=url, basis=basis, license=lic[0], licenseUrl=lic[1], note=note, fit=fit, pos=pos)

def uton(file, title, url, **kw):
    return art(file, title, UTON['author'], UTON['page'], url, UTON['basis'], UTON['lic'], UTON['note'], **kw)

MEDIA = {
 '002': art('002-a', 'SCP-002 article image (composite)', 'SCP-002 article image; components: The Metropolitan Museum of Art (public domain) and two CC0 photos (pxhere, peakpx)', W + 'scp-002', 'https://scp-wiki.wdfiles.com/local--files/scp-002/800px-SCP002-new.jpg', lic=('Public domain / CC0 components (article CC BY-SA 3.0)', 'https://creativecommons.org/licenses/by-sa/3.0/')),
 '008': art('008-a', 'scp-008.png (article image)', 'EstrellaYoshte; derivative of "Protein BLMH PDB 1cb5" by Emw (CC BY-SA 3.0)', W + 'scp-008', 'https://scp-wiki.wdfiles.com/local--files/scp-008/scp-008.png', fit='contain'),
 '012': uton('012-a', 'SCP-012 "A Bad Composition" postcard', 'https://scp-jp-storage.wdfiles.com/local--files/file:10359876-9-ffku/IMG_4115.jpeg', pos='50% 30%'),
 '035': art('035-a', 'scp--035--002-new.gif (article image)', 'VolgunStrife', W + 'scp-035', 'https://scp-wiki.wdfiles.com/local--files/scp-035/scp--035--002-new.gif'),
 '049': art('049-a', '049_1_ntsc.png (article image)', 'VolgunStrife', W + 'scp-049', 'https://scp-wiki.wdfiles.com/local--files/scp-049/049_1_ntsc.png'),
 '053': art('053-a', 'SCP-0053.jpg (article image)', 'Escape from Site 19', W + 'scp-053', 'https://scp-wiki.wdfiles.com/local--files/scp-053/SCP-0053.jpg', pos='78% 30%'),
 '055': art('055-a', 'SCP-055 illustration', 'DrKens', W + 'kens-artistic-side', 'https://scp-wiki.wikidot.com/local--files/kens-artistic-side/cjU6b.webp', basis='page-license', note='Artist page "Kens\' Artistic Side" by DrKens; page licensed CC BY-SA, no per-file entry found.'),
 '073': art('073-a', 'scp-073.jpg', 'PanLing (translated page by la kanro)', W + 'panling-scp', 'https://scp-wiki.wdfiles.com/local--files/panling-scp/scp-073.jpg', note='License box source: SCP Foundation Wiki CN Branch.'),
 '076': art('076-a', 'Run Abel (visual arts competition entry)', 'julia P', W + 'art:artwork-076', 'https://scp-wiki.wdfiles.com/local--files/art:artwork-076/run_abel__by_nayafenix_dhbsodq-375w-2x.jpg', pos='50% 25%'),
 '079': art('079-c', 'SCP-079 (SCP - Containment Breach)', 'Joonas Rikkonen (Regalis), SCP – Containment Breach', 'https://commons.wikimedia.org/wiki/File:SCP-079_(SCP_-_Containment_Breach).jpg', 'https://upload.wikimedia.org/wikipedia/commons/d/db/SCP-079_%28SCP_-_Containment_Breach%29.jpg', basis='commons', lic=BY3, note='Commons lists CC BY 3.0. The game itself is CC BY-SA 3.0.'),
 '087': art('087-a', '087face.jpg (article image)', 'CityToast', W + 'scp-087', 'https://scp-wiki.wdfiles.com/local--files/scp-087/087face.jpg'),
 '093': art('093-f', 'SCP-093 (Art Contest, Series 1)', 'JC', W + 'art-contest-hub-series-1', 'https://i.imgur.com/fgv7B4l.png', basis='page-license', note='Art contest hub entry; the hub credits the artist and links this fullview. No per-file license-box entry.'),
 '096': art('096-c', 'SCP-096 (SCP - Containment Breach)', 'SCP – Containment Breach (Joonas Rikkonen and contributors)', 'https://commons.wikimedia.org/wiki/File:SCP-096_(SCP_-_Containment_Breach).jpg', 'https://upload.wikimedia.org/wikipedia/commons/3/3f/SCP-096_%28SCP_-_Containment_Breach%29.jpg', basis='commons'),
 '106': art('106-a', 'Emergence (106emergenceklay.jpg)', 'Klay Abele / MrKlay', W + 'scp-106', 'https://scp-wiki.wdfiles.com/local--files/scp-106/106emergenceklay.jpg'),
 '131': art('131-a', '131volgun.png (article image)', 'VolgunStrife', W + 'scp-131', 'https://scp-wiki.wdfiles.com/local--files/scp-131/131volgun.png', fit='contain'),
 '173': art('173-c', 'SCP CB First encounter of SCP-173', 'SCP – Containment Breach; screenshot by SpectraKo', 'https://commons.wikimedia.org/wiki/File:SCP_CB_First_encounter_of_SCP-173.png', 'https://upload.wikimedia.org/wikipedia/commons/8/8f/SCP_CB_First_encounter_of_SCP-173.png', basis='commons', note='Game render of SCP-173. Deliberately not the Izumi Kato "Untitled 2004" sculpture photo, which is not freely licensed.'),
 '294': art('294-a', 'SCP-294 (article image)', 'StaticFactory', W + 'scp-294', 'https://scp-wiki.wdfiles.com/local--files/scp-294/scp_294_by_staticfactory-d4xwn6e.jpg'),
 '343': art('343-a', 'ruraart.jpg', 'RuraScarlet', W + 'tell-me-all-your-thoughts-on-god', 'https://scp-wiki.wdfiles.com/local--files/tell-me-all-your-thoughts-on-god/ruraart.jpg', note='From the SCP-343 tale "Tell Me All Your Thoughts On God" by Doctor Cimmerian.'),
 '354': art('354-a', 'redpool-new.jpg (article image)', 'stephlynch, Jim Sorbie; derivative of "DSC_7396 copy" by Jim Sorbie (CC BY 2.0)', W + 'scp-354', 'https://scp-wiki.wdfiles.com/local--files/scp-354/redpool-new.jpg'),
 '426': art('426-a', 'SCP-426 illustration (KuruG)', 'DrKens', W + 'kens-artistic-side', 'https://scp-wiki.wikidot.com/local--files/kens-artistic-side/KuruG.webp', basis='page-license', note='Artist page by DrKens; page licensed CC BY-SA, no per-file entry found.'),
 '500': uton('500-a', 'SCP-500 "Panacea" postcard', 'https://scp-jp-storage.wdfiles.com/local--files/file:10359876-13-50o7/IMG_5732.jpeg', pos='72% 40%'),
 '513': uton('513-u', 'SCP-513 "A Cowbell" postcard', 'https://scp-jp-storage.wdfiles.com/local--files/file:10359876-13-zs2l/IMG_5733.jpeg', pos='50% 25%'),
 '610': art('610-a', '610-new.png (article image)', 'stephlynch, Austin Beaulier; derivative of "My dog Sookie sleeping" by Austin Beaulier (CC BY 4.0)', W + 'scp-610', 'https://scp-wiki.wdfiles.com/local--files/scp-610/610-new.png'),
 '682': art('682-a', 'monster8editub9-new.jpg (article image)', 'OccultistMave; derivative of a photo by Paxson Woelber (CC BY 2.0)', W + 'scp-682', 'https://scp-wiki.wdfiles.com/local--files/scp-682/monster8editub9-new.jpg'),
 '701': art('701-a', 'Volgun701.jpg (article image)', 'VolgunStrife', W + 'scp-701', 'https://scp-wiki.wdfiles.com/local--files/scp-701/Volgun701.jpg'),
 '914': art('914-c', 'SCP-914 (SCP - Containment Breach)', 'Image by Cridone, from SCP – Containment Breach by Joonas "Regalis" Rikkonen', 'https://commons.wikimedia.org/wiki/File:SCP-914_(SCP_-_Containment_Breach).png', 'https://upload.wikimedia.org/wikipedia/commons/a/aa/SCP-914_%28SCP_-_Containment_Breach%29.png', basis='commons', fit='contain'),
 '939': art('939-c', 'SCP-939 (SCP: Secret Laboratory)', 'Northwood Studios', 'https://commons.wikimedia.org/wiki/File:SCP-939.jpg', 'https://upload.wikimedia.org/wikipedia/commons/d/db/SCP-939.jpg', basis='commons', lic=BY3),
 '966': art('966-a', 'Darkskullteeth infrared (article image)', 'stephlynch', W + 'scp-966', 'https://scp-wiki.wdfiles.com/local--files/scp-966/Darkskullteeth%20infrared%201-new.png'),
 '999': art('999-f', 'SCP-999 (Art Contest, Series 1)', 'drakull232', W + 'art-contest-hub-series-1', 'https://i.imgur.com/h0vFlax.png', basis='page-license', note='Art contest hub entry; fullview linked from the hub. No per-file license-box entry.'),
 '1048': art('1048-f', 'SCP-1048 (Art Contest, Series 2)', 'DaeriusD', W + 'art-contest-hub-series-2', 'https://i.imgur.com/sRneH1D.png', basis='page-license', note='Art contest hub entry; fullview linked from the hub. No per-file license-box entry.'),
 '1471': art('1471-a', 'SCP1471.jpg (article image)', 'Tanagryph (mask by Clockwork Creature)', W + 'scp-1471', 'https://scp-wiki.wdfiles.com/local--files/scp-1471/scp1471.jpg', lic=('CC BY-SA', 'https://creativecommons.org/licenses/by-sa/3.0/')),
 '2006': art('2006-a', 'SCP-2006 "Too Spooky" (artchive file)', 'Dr Avenlee', W + 'art:dr-avenlee-s-artchives', 'https://scp-wiki.wikidot.com/local--files/art:dr-avenlee-s-artchives/SCP-2006', basis='page-license', note='The SCP-2006 article image is copyrighted and used with permission, so it was not reused. This is fan art from a CC BY-SA artist page.'),
 '2317': art('2317-f', 'SCP-2317 (Art Contest, Series 3)', 'Kenoma', W + 'art-contest-hub-series-3', 'https://i.imgur.com/QIjBxpi.png', basis='page-license', note='Art contest hub entry; fullview linked from the hub. No per-file license-box entry.'),
 '2521': art('2521-f', 'SCP-2521 (Art Contest, Series 3)', 'Phillip Schaffield', W + 'art-contest-hub-series-3', 'https://i.imgur.com/DN3x2T1.png', basis='page-license', note='The SCP-2521 article images are copyrighted and used with permission, so they were not reused. Fullview linked from the art contest hub.'),
 '3000': art('3000-w', 'SCP-3000 watercolour', 'bloodandheart (artist named in the file name)', W + 'art:anomalies-in-water-colour', 'https://scp-wiki.wikidot.com/local--files/art:anomalies-in-water-colour/scp_3000_in_water_colour_by_bloodandheart_dfqm73q-pre.webp', basis='page-license', note='From the artist page "Anomalies in water colour". The page footer states CC BY-SA 3.0; no license box or per-file entry was found.', pos='18% 40%'),
 '3008': art('3008-f', 'SCP-3008-2 (Art Contest, Series 4)', 'HiuMentah', W + 'art-contest-hub-series-4', 'https://i.imgur.com/oPVD9NB.png', basis='page-license', note='Art contest hub entry; fullview linked from the hub. No per-file license-box entry.'),
}

import json
from pathlib import Path
from common.srtools import FreesrData

SERVER_DIR = Path(__file__).resolve().parent

def generate():
    with open(SERVER_DIR / 'freesr-data.json', encoding='utf-8') as f:
        raw = json.load(f)

    with open('G:/sf/LunarCore/resources/ExcelOutput/AvatarConfig.json', encoding='utf-8') as f:
        avatar_configs = {x['AvatarID']: x for x in json.load(f)}
    ld_cfg_path = Path('G:/sf/LunarCore/resources/ExcelOutput/AvatarConfigLD.json')
    if ld_cfg_path.exists():
        with open(ld_cfg_path, encoding='utf-8') as f:
            for x in json.load(f):
                avatar_configs[x['AvatarID']] = x

    with open('G:/sf/LunarCore/resources/ExcelOutput/AvatarSkillTreeConfig.json', encoding='utf-8') as f:
        skill_tree = json.load(f)
    ld_tree_path = Path('G:/sf/LunarCore/resources/ExcelOutput/AvatarSkillTreeConfigLD.json')
    if ld_tree_path.exists():
        with open(ld_tree_path, encoding='utf-8') as f:
            skill_tree.extend(json.load(f))

    tree_by_avatar = {}
    for entry in skill_tree:
        aid = entry.get('AvatarID')
        pid = entry.get('PointID')
        lvl = entry.get('Level', 1)
        if aid not in tree_by_avatar:
            tree_by_avatar[aid] = {}
        if pid not in tree_by_avatar[aid] or lvl > tree_by_avatar[aid][pid]:
            tree_by_avatar[aid][pid] = lvl

    with open('G:/sf/LunarCore/resources/ExcelOutput/AvatarEquipRecommend.json', encoding='utf-8') as f:
        equip_recommends = {x['AvatarID']: x['EquipmentList'] for x in json.load(f)}
    ld_equip_path = Path('G:/sf/LunarCore/resources/ExcelOutput/AvatarEquipRecommendLD.json')
    if ld_equip_path.exists():
        with open(ld_equip_path, encoding='utf-8') as f:
            for x in json.load(f):
                equip_recommends[x['AvatarID']] = x['EquipmentList']

    with open(SERVER_DIR / 'common/res/avatarConfigs.json', encoding='utf-8') as f:
        echium_avatar_configs = json.load(f)['avatarConfigs']

    with open('G:/sf/LunarCore/resources/ExcelOutput/RelicConfig.json', encoding='utf-8') as f:
        relic_configs = {r['ID']: r for r in json.load(f) if r.get('Rarity') == 'CombatPowerRelicRarity5'}

    with open('G:/sf/LunarCore/resources/ExcelOutput/RelicMainAffixConfig.json', encoding='utf-8') as f:
        main_affix_list = json.load(f)

    main_affix_map = {}
    for aff in main_affix_list:
        gid = aff['GroupID']
        prop = aff['Property']
        aid = aff['AffixID']
        main_affix_map.setdefault(gid, {})[prop] = aid

    with open('G:/sf/LunarCore/resources/ExcelOutput/AvatarRelicRecommend.json', encoding='utf-8') as f:
        relic_recommends = {x['AvatarID']: x for x in json.load(f)}
    ld_relic_path = Path('G:/sf/LunarCore/resources/ExcelOutput/AvatarRelicRecommendLD.json')
    if ld_relic_path.exists():
        with open(ld_relic_path, encoding='utf-8') as f:
            for x in json.load(f):
                relic_recommends[x['AvatarID']] = x

    anchor_skills = {str(i): 1 for i in range(1, 19)}
    anchor_skills = {str(i): 1 for i in range(1, 23)}
    anchor_skills['1'] = 6
    anchor_skills['2'] = 10
    anchor_skills['3'] = 10
    anchor_skills['4'] = 10
    anchor_skills['19'] = 6
    anchor_skills['20'] = 6
    anchor_skills['22'] = 10

    avatars = {}
    for aid, cfg in avatar_configs.items():
        sp_need = cfg.get('SPNeed', {}).get('Value', 100)
        echium_cfg = echium_avatar_configs.get(str(aid), {})
        techs = echium_cfg.get('techniqueBuffIds', [aid * 100 + 1])

        pts = {str(k): v for k, v in tree_by_avatar.get(aid, {}).items() if str(k).startswith(str(aid))}
        if not pts:
            pts = {
                str(n): 1 for n in (
                    *range(aid * 1000 + 1, aid * 1000 + 5),
                    aid * 1000 + 7,
                    *range(aid * 1000 + 101, aid * 1000 + 104),
                    *range(aid * 1000 + 201, aid * 1000 + 211),
                )
            }
            pts[str(aid * 1000 + 1)] = 6
            pts[str(aid * 1000 + 2)] = 10
            pts[str(aid * 1000 + 3)] = 10
            pts[str(aid * 1000 + 4)] = 10

        existing_av = raw.get('avatars', {}).get(str(aid), {})
        dressed_skin = existing_av.get('dressed_skin_id', 0)
        default_skins = {
            1001: 1100101,
            1303: 1130301,
            1310: 1131001,
            1407: 1140701,
            1415: 1141501,
            1501: 1150101,
        }
        if not dressed_skin and aid in default_skins:
            dressed_skin = default_skins[aid]

        avatars[str(aid)] = {
            'avatar_id': aid,
            'data': {
                'rank': 6,
                'skills': pts,
                'skills_by_anchor_type': anchor_skills
            },
            'level': 80,
            'promotion': 6,
            'sp_max': sp_need,
            'sp_value': 0,
            'techniques': techs,
            'enhanced_id': None,
            'dressed_skin_id': dressed_skin
        }

    # Lightcones
    existing_lcs = raw.get('lightcones', [])
    equipped_aids = {lc['equip_avatar'] for lc in existing_lcs}
    lightcones = list(existing_lcs)

    max_uid = max([lc.get('internal_uid', 0) for lc in lightcones] + [3000])
    uid_counter = max(max_uid + 1, 3001)

    for aid in avatar_configs.keys():
        if aid not in equipped_aids:
            rec_list = equip_recommends.get(aid, [])
            item_id = rec_list[0] if rec_list else 23000
            lightcones.append({
                'equip_avatar': aid,
                'internal_uid': uid_counter,
                'item_id': item_id,
                'level': 80,
                'promotion': 6,
                'rank': 5
            })
            uid_counter += 1

    # Relics
    slot_to_group = {1: 51, 2: 52, 3: 53, 4: 54, 5: 55, 6: 56}
    type_to_slot = {'HEAD': 1, 'HAND': 2, 'BODY': 3, 'FOOT': 4, 'NECK': 5, 'OBJECT': 6}
    prop_to_subaffix = {
        'HPDelta': 1, 'AttackDelta': 2, 'DefenceDelta': 3, 'HPAddedRatio': 4,
        'AttackAddedRatio': 5, 'DefenceAddedRatio': 6, 'SpeedDelta': 7,
        'CriticalChanceBase': 8, 'CriticalDamageBase': 9, 'StatusProbabilityBase': 10,
        'StatusResistanceBase': 11, 'BreakDamageAddedRatioBase': 12,
    }

    relics = []
    relic_uid = 1

    for aid in avatar_configs.keys():
        rec = relic_recommends.get(aid, {})
        set4 = rec['Set4IDList'][0] if rec.get('Set4IDList') else 101
        set2 = rec['Set2IDList'][0] if rec.get('Set2IDList') else 301

        prop_map = {}
        for p in rec.get('PropertyList', []):
            rtype = p.get('RelicType')
            ptype = p.get('PropertyType')
            if rtype in type_to_slot:
                prop_map[type_to_slot[rtype]] = ptype

        sub_props = rec.get('SubAffixPropertyList', [])
        preferred_sub_ids = []
        for sp in sub_props:
            if sp in prop_to_subaffix and prop_to_subaffix[sp] not in preferred_sub_ids:
                preferred_sub_ids.append(prop_to_subaffix[sp])

        for fallback in [8, 9, 7, 5, 4, 12, 10]:
            if len(preferred_sub_ids) >= 4:
                break
            if fallback not in preferred_sub_ids:
                preferred_sub_ids.append(fallback)

        chosen_subs = preferred_sub_ids[:4]
        sub_affixes = [
            {'count': 1, 'step': 2, 'sub_affix_id': chosen_subs[0]},
            {'count': 3, 'step': 6, 'sub_affix_id': chosen_subs[1]},
            {'count': 3, 'step': 6, 'sub_affix_id': chosen_subs[2]},
            {'count': 1, 'step': 2, 'sub_affix_id': chosen_subs[3]},
        ]

        for slot in range(1, 7):
            set_id = set4 if slot <= 4 else set2
            relic_id = 60000 + set_id * 10 + slot
            if relic_id not in relic_configs:
                set_id = 101 if slot <= 4 else 301
                relic_id = 60000 + set_id * 10 + slot

            gid = slot_to_group[slot]
            prop = prop_map.get(slot)
            main_affix_id = main_affix_map.get(gid, {}).get(prop, 1)

            relics.append({
                'equip_avatar': aid,
                'internal_uid': relic_uid,
                'level': 15,
                'relic_id': relic_id,
                'main_affix_id': main_affix_id,
                'relic_set_id': set_id,
                'sub_affixes': sub_affixes
            })
            relic_uid += 1

    # Extra spare unequipped relics for commonly used sets
    popular_set4s = [101, 102, 103, 104, 105, 106, 108, 111, 112, 117, 119, 122, 126, 128, 129]
    popular_set2s = [301, 303, 304, 306, 307, 309, 310, 312, 313, 314, 316, 317, 324, 325]

    for s4 in popular_set4s:
        for slot in range(1, 5):
            rid = 60000 + s4 * 10 + slot
            if rid in relic_configs:
                gid = slot_to_group[slot]
                # Default best main affixes: Body CRIT Rate (4), Feet SPD (4)
                mid = 4 if slot in (3, 4) else 1
                relics.append({
                    'equip_avatar': 0,
                    'internal_uid': relic_uid,
                    'level': 15,
                    'relic_id': rid,
                    'main_affix_id': mid,
                    'relic_set_id': s4,
                    'sub_affixes': [
                        {'count': 1, 'step': 2, 'sub_affix_id': 8},
                        {'count': 3, 'step': 6, 'sub_affix_id': 9},
                        {'count': 3, 'step': 6, 'sub_affix_id': 7},
                        {'count': 1, 'step': 2, 'sub_affix_id': 5},
                    ]
                })
                relic_uid += 1

    for s2 in popular_set2s:
        for slot in (5, 6):
            rid = 60000 + s2 * 10 + slot
            if rid in relic_configs:
                gid = slot_to_group[slot]
                # Default best main affixes: Neck ATK% (2), Object Energy Regen (2)
                mid = 2
                relics.append({
                    'equip_avatar': 0,
                    'internal_uid': relic_uid,
                    'level': 15,
                    'relic_id': rid,
                    'main_affix_id': mid,
                    'relic_set_id': s2,
                    'sub_affixes': [
                        {'count': 1, 'step': 2, 'sub_affix_id': 8},
                        {'count': 3, 'step': 6, 'sub_affix_id': 9},
                        {'count': 3, 'step': 6, 'sub_affix_id': 7},
                        {'count': 1, 'step': 2, 'sub_affix_id': 5},
                    ]
                })
                relic_uid += 1

    out_data = dict(raw)
    out_data['avatars'] = avatars
    out_data['lightcones'] = lightcones
    out_data['relics'] = relics

    # Validate with FreesrData model
    validated = FreesrData.model_validate(out_data)

    target_file = SERVER_DIR / 'freesr-data.json'
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(validated.model_dump_json(indent=2))

    print(f'Successfully generated {len(avatars)} avatars, {len(lightcones)} lightcones, and {len(relics)} relics to {target_file}')

if __name__ == '__main__':
    generate()

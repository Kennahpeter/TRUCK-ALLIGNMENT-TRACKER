from django.db import migrations

FLEET = [
    ("KDK 494Z", "ZH 0565"),
    ("KDK 496Z", "ZH 0566"),
    ("KDK 497Z", "ZH 0567"),
    ("KDM 129V", "ZH 2309"),
    ("KDM 142V", "ZH 2310"),
    ("KDM 143V", "ZH 2311"),
    ("KDN 353L", "ZF 8141"),
    ("KDN 354L", "ZH 0565"),
    ("KDQ 037Q", "ZH 4783"),
    ("KDQ 917P", "ZH 4777"),
    ("KDQ 918P", "ZH 4770"),
    ("KDQ 920P", "ZH 4769"),
    ("KDQ 921P", "ZH 4771"),
    ("KDQ 923P", "ZH 4782"),
    ("KDQ 924P", "ZH 4781"),
    ("KDQ 926P", "ZH 4778"),
    ("KDQ 927P", "ZH 4779"),
    ("KDQ 928P", "ZH 4772"),
    ("KDR 516N", "ZH 5863"),
    ("KDR 517N", "ZH 5855"),
    ("KDR 518N", "ZH 5858"),
    ("KDR 519N", "ZH 5861"),
    ("KDR 522N", "ZH 5857"),
    ("KDR 523N", "ZH 5866"),
    ("KDR 526N", "ZH 5862"),
    ("KDR 527N", "ZH 5867"),
    ("KDR 529N", "ZH 5860"),
    ("KDR 575N", "ZH 5864"),
    ("KDR 682N", "ZH 5856"),
    ("KDR 684N", "ZH 5865"),
    ("KDW 689S", "ZJ 1667"),
    ("KDW 695S", "ZJ 1669"),
    ("KDW 699S", "ZJ 1668"),
    ("KDW 702S", "ZJ 1666"),
    ("KDW 703S", "ZH 8021"),
    ("KDW 704S", "ZJ 1696"),
    ("KDW 722S", "ZF 8134"),
    ("KDX 262T", "ZJ 3267"),
    ("KDX 263T", "ZJ 3268"),
    ("KDX 264T", "ZJ 3264"),
    ("KDX 265T", "ZJ 3265"),
    ("KDX 270T", "ZJ 3267"),
    ("KDX 271T", "ZJ 3266"),
    ("KDX 816K", "ZJ 2414"),
    ("KDX 823K", "ZJ 2413"),
    ("KDX 824K", "ZJ 2341"),
    ("KDX 828L", "ZG 1386"),
    ("KDX 829K", "ZJ 2342"),
    ("KDX 830K", "ZJ 2344"),
    ("KDX 831K", "ZJ 2343"),
    ("KDY 387E", "ZH 4780"),
]


def seed_fleet(apps, schema_editor):
    Truck = apps.get_model('alignments', 'Truck')
    for truck_id, trailer_id in FLEET:
        Truck.objects.get_or_create(
            truck_id=truck_id,
            defaults={'trailer_id': trailer_id, 'active': True},
        )


def unseed_fleet(apps, schema_editor):
    Truck = apps.get_model('alignments', 'Truck')
    Truck.objects.filter(truck_id__in=[t for t, _ in FLEET]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('alignments', '0002_truck'),
    ]

    operations = [
        migrations.RunPython(seed_fleet, unseed_fleet),
    ]

# Meeting Scheduler Bot

"5;53@0<-1>B 4;O 02B><0B870F88 ?;0=8@>20=8O 2AB@5G A @C:>2>48B5;O<8 >B45;>2.

## A=>2=K5 2>7<>6=>AB8

- =Å 2B><0B8G5A:0O ?@>25@:0 4>ABC?=>AB8 A;>B>2 2 Google Calendar
- =e !8AB5<0 @538AB@0F88 A 0?@C2>< 04<8=8AB@0B>@><
- <4 #?@02;5=85 >B?CA:0<8/1>;L=8G=K<8
- = #<=K5 =0?><8=0=8O (7 4=59, 3 4=O, 1 45=L, 1 G0A)
- =Ê !B0B8AB8:0 2AB@5G
- < Webhook 4;O <3=>25==>3> >1=>2;5=8O 70=OB>AB8

## "@51>20=8O

- Python 3.10+
- PostgreSQL
- Google Cloud 0::0C=B A 2:;NG5==K< Google Calendar API
- Telegram Bot Token

## #AB0=>2:0 8 =0AB@>9:0

### 1. ;>=8@>20=85 @5?>78B>@8O

```bash
git clone https://github.com/patriot-33/meeting-scheduler-bot.git
cd meeting-scheduler-bot
```

### 2. !>740=85 28@BC0;L=>3> >:@C65=8O

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 8;8
venv\Scripts\activate  # Windows
```

### 3. #AB0=>2:0 7028A8<>AB59

```bash
pip install -r requirements.txt
```

### 4. 0AB@>9:0 Google Calendar API

1. 5@5948B5 =0 [Google Cloud Console](https://console.cloud.google.com/)
2. !>7409B5 =>2K9 ?@>5:B 8;8 2K15@8B5 ACI5AB2CNI89
3. :;NG8B5 Google Calendar API
4. !>7409B5 Service Account
5. !:0G09B5 JSON :;NG 8 A>E@0=8B5 :0: `service_account_key.json`
6. @54>AB02LB5 4>ABC? Service Account : 20H8< :0;5=40@O<

### 5. 0AB@>9:0 ?5@5<5==KE >:@C65=8O

```bash
cp .env.example .env
```

B@540:B8@C9B5 `.env` D09; A 20H8<8 40==K<8.

### 6. =8F80;870F8O 107K 40==KE

```bash
python -m src.database
```

### 7. 0?CA: 1>B0

```bash
python -m src.main
```

##  0725@BK20=85 =0 Render.com

1. !>7409B5 PostgreSQL 107C 40==KE
2. !>7409B5 Web Service 8 A2O68B5 A MB8< @5?>78B>@85<
3. >102LB5 ?5@5<5==K5 >:@C65=8O
4. Deploy!

## ><0=4K 1>B0

### ;O 2A5E ?>;L7>20B5;59
- `/start` - 0G0;> @01>BK
- `/register` -  538AB@0F8O
- `/help` - ><>IL

### ;O @C:>2>48B5;59
- `/schedule` - >A<>B@5BL 4>ABC?=K5 A;>BK
- `/my_meetings` - >8 2AB@5G8
- `/vacation` - B<5B8BL >B?CA:
- `/sick` - B<5B8BL 1>;L=8G=K9
- `/active` - 5@=CBLAO 2 0:B82=K9 AB0BCA

### ;O 04<8=8AB@0B>@>2
- `/admin` - 4<8=-?0=5;L
- `/pending` - 6840NI85 0?@C20
- `/users` - !?8A>: ?>;L7>20B5;59
- `/stats` - !B0B8AB8:0
- `/notifications` - :;/2K:; C254><;5=8O
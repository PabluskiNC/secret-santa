Intro
=====

**secret-santa** can help you manage a list of secret santa participants by
randomly assigning pairings and sending emails. It can avoid pairing
couples to their significant other, and allows custom email messages to be
specified.

Dependencies
------------
```
# optional: conda create -n secret-santa python=3.11
#           conda activate secret-santa
pip install -r requirements.txt
```

In 2020 we upgraded this slightly to work with Python 3.5.2!
'Cause that was the latest version that pyenv would install on Ben's old iMac.

Config
-----

Each year, create a new folder for the year, like 2020, 2021, etc.

Copy and modify a new config file, like `2021/2021-config.yml`, for example.

Edit participants, "dont pair", and "don't repeat" config based on email responses this year.

Edit the email template if that seems fun!

Update the year in the outgoing `SUBJECT:` line:
```
    SUBJECT: Your official [Current-year-here] Consortium 2.0
```

Update connection details for sending the emails.

In 2020 Ben set up an "App" at Google to get a Mail-specific password to use.
Something like this otta work again.
See [here](https://support.google.com/accounts/answer/185833?p=InvalidSecondFactor&visit_id=637410814259150647-336572923&rd=1).

Go Time
-----

In 2021 Ben modified this to work in two separate steps.

The first step generates the pairings and saves them to a yaml file.
```
python secret_santa.py --config 2023/2023-config.yml --pairings 2023/2023-pairings.yml
```

Paste that output unto [GraphViz Online](https://dreampuf.github.io/GraphvizOnline/) with a little

```
node[color="indianred3" style="filled" shape="rounded" fontcolor="green"]
edge[color="darkolivegreen"]
```

And have yourself a great time!

Run this as many times as needed.
Edit this by hand if you're up for it.
Review this before sending!

To go ahead and send the emails for realzies:
```
python secret_santa.py --config 2023/2023-config.yml --pairings 2023/2023-pairings.yml --send
```

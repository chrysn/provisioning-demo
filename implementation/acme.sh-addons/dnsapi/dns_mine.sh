#!/usr/bin/env sh

########  Public functions #####################

#Usage: dns_mine_add   _acme-challenge.www.domain.com   "XKrxpRBosdIKFzxW_CT3KLZNf6q0HG9i01zxXp5CPBs"
dns_mine_add() {
  fulldomain=$1
  txtvalue=$2
  [ -n "${KNOT_SERVER}" ] || KNOT_SERVER="localhost"
  # save the dns server and key to the account.conf file.
  _saveaccountconf KNOT_SERVER "${KNOT_SERVER}"
  _saveaccountconf KNOT_KEY "${KNOT_KEY}"

  _info "Trusting you added ${fulldomain}. 60 TXT \"${txtvalue}\""

  echo -n "${txtvalue}" > /tmp/token

  return 0
}

#Usage: dns_mine_rm   _acme-challenge.www.domain.com
dns_mine_rm() {
  return 0
}

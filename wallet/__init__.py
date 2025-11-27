default_app_config = 'wallet.apps.WalletConfig'


def get_percentage(amount):
	const = 1.5
	per = 0
	if amount > 500000:
		per = (0.5 + const)/100
	else:
		per = (5 - const)/100
	return amount * per



def on_pre_page_macros(env):
	global meta_date
	if 'date' in env.page.meta:
		meta_date = env.page.meta['date']
	else: meta_date = ''


def define_env(env):
	
	@env.macro
	def date():
		return f''

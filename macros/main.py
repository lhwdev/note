

def on_pre_page_macros(env):
	global meta_date
	meta_date = env.page.meta.date


def define_env(env):
	
	@env.macro
	def date():
		return f''

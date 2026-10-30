from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from .models import User, PasswordResetCode


class ContactRequestForm(forms.Form):
    name = forms.CharField(max_length=120)
    phone = forms.CharField(max_length=30)
    message = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Maslahat yoki kamchilikni yozing...', 'rows': 5, 'class': 'message-textarea'}))
    telegram_id = forms.CharField(required=False, widget=forms.HiddenInput())
    telegram_username = forms.CharField(required=False, widget=forms.HiddenInput())


class UserRegisterForm(UserCreationForm):
	email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Elektron pochta mansili'}))

	class Meta(UserCreationForm.Meta):
		model = User
		fields = ('username', 'email')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for field in self.fields.values():
			field.widget.attrs.update({'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition'})


class UserProfileForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ('email', 'telegram_id', 'avatar')
		widgets = {
			'email': forms.EmailInput(attrs={'placeholder': 'Elektron pochta manzili', 'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition'}),
			'telegram_id': forms.TextInput(attrs={'placeholder': 'Telegram ID (masalan: 8295295427)', 'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition'}),
			'avatar': forms.ClearableFileInput(attrs={
				'accept': 'image/*',
				'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition',
			}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if 'email' in self.fields:
			self.fields['email'].required = False
		if 'telegram_id' in self.fields:
			self.fields['telegram_id'].required = False
		if 'avatar' in self.fields:
			self.fields['avatar'].required = False


class OptionalPasswordChangeForm(PasswordChangeForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		for field_name in ('old_password', 'new_password1', 'new_password2'):
			if field_name in self.fields:
				self.fields[field_name].required = False
				self.fields[field_name].widget.attrs.update({
					'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition'
				})

	def clean(self):
		cleaned_data = super().clean()
		old_password = cleaned_data.get('old_password')
		new_password1 = cleaned_data.get('new_password1')
		new_password2 = cleaned_data.get('new_password2')

		if not any([old_password, new_password1, new_password2]):
			return cleaned_data

		if not old_password:
			self.add_error('old_password', 'Eski parolni kiriting.')
		if not new_password1:
			self.add_error('new_password1', 'Yangi parolni kiriting.')
		if not new_password2:
			self.add_error('new_password2', 'Parolni tasdiqlang.')

		if old_password and not self.user.check_password(old_password):
			self.add_error('old_password', 'Eski parol noto`g`ri.')

		if new_password1 and new_password2 and new_password1 != new_password2:
			self.add_error('new_password2', 'Yangi parollar mos kelmadi.')

		return cleaned_data


class UserLoginForm(AuthenticationForm):
	username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Foydalanuvchi nomi', 'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition'}))
	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Parol', 'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition'}))


class PasswordResetRequestForm(forms.Form):
	email = forms.EmailField(
		label='Elektron pochta',
		widget=forms.EmailInput(attrs={
			'placeholder': 'Elektron pochtangizni kiriting',
			'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition',
			'autocomplete': 'email',
			'id': 'reset-email-input',
		})
	)

	def clean_email(self):
		email = self.cleaned_data.get('email', '').strip().lower()
		if not User.objects.filter(email__iexact=email, is_active=True).exists():
			raise forms.ValidationError('Ushbu elektron pochta manziliga ega faol foydalanuvchi topilmadi.')
		return email


class PasswordResetConfirmForm(forms.Form):
	code = forms.CharField(
		max_length=6,
		min_length=6,
		label='6 xonali tasdiqlash kodi',
		widget=forms.TextInput(attrs={
			'placeholder': '123456',
			'maxlength': '6',
			'pattern': '[0-9]{6}',
			'inputmode': 'numeric',
			'class': 'w-full px-4 py-3 text-center text-3xl tracking-[0.35em] font-mono font-bold rounded-xl border-2 border-slate-300 focus:ring-2 focus:ring-[#5c4683] focus:border-[#5c4683] outline-none transition bg-slate-50 text-slate-800',
			'autocomplete': 'one-time-code',
			'id': 'reset-code-input',
		})
	)
	new_password1 = forms.CharField(
		label='Yangi parol',
		widget=forms.PasswordInput(attrs={
			'placeholder': 'Kamida 8 ta belgi',
			'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition',
			'autocomplete': 'new-password',
			'id': 'reset-pass1-input',
		})
	)
	new_password2 = forms.CharField(
		label='Yangi parolni tasdiqlang',
		widget=forms.PasswordInput(attrs={
			'placeholder': 'Parolni qaytadan kiriting',
			'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition',
			'autocomplete': 'new-password',
			'id': 'reset-pass2-input',
		})
	)

	def __init__(self, user, *args, **kwargs):
		self.user = user
		self.reset_code_obj = None
		super().__init__(*args, **kwargs)

	def clean_code(self):
		code = self.cleaned_data.get('code', '').replace(' ', '').replace('-', '').strip()
		if not code.isdigit() or len(code) != 6:
			raise forms.ValidationError('Tasdiqlash kodi aynan 6 xonali raqamdan iborat bo‘lishi kerak.')

		reset_code = PasswordResetCode.objects.filter(
			user=self.user,
			code=code
		).order_by('-created_at').first()

		if not reset_code:
			raise forms.ValidationError('Kiritilgan 6 xonali tasdiqlash kodi noto‘g‘ri.')

		if reset_code.is_used:
			raise forms.ValidationError('Ushbu kod allaqachon ishlatilgan. Yangi kod so‘rang.')

		if reset_code.is_expired():
			raise forms.ValidationError('Tasdiqlash kodining 10 daqiqalik amal qilish muddati tugagan. Iltimos, yangi kod so‘rang.')

		self.reset_code_obj = reset_code
		return code

	def clean(self):
		cleaned_data = super().clean()
		p1 = cleaned_data.get('new_password1')
		p2 = cleaned_data.get('new_password2')

		if p1 and p2:
			if p1 != p2:
				self.add_error('new_password2', 'Yangi parollar bir-biriga mos kelmadi.')
			else:
				try:
					validate_password(p1, self.user)
				except forms.ValidationError as error:
					self.add_error('new_password1', error)
		return cleaned_data

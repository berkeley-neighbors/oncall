var oncallSplash = {
  data: {
    $loginForm: $("#login-form"),
    $synologySsoLogin: $("#synology-sso-login"),
    loginUrl: "/login",
    csrfKey: "csrf-key",
  },
  callbacks: {
    onLogin: function (data) {
      // callback for successful user login. Reloads page to go to the normal oncall interface.
      location.reload();
    },
  },
  init: function () {
    this.events();
  },
  login: function (e) {
    e.preventDefault();
    var url = this.data.loginUrl,
      $form = this.data.$loginForm,
      self = this;

    $.ajax({
      url: url,
      type: "POST",
      data: $form.serialize(),
      dataType: "html",
    })
      .done(function (data) {
        var data = JSON.parse(data),
          token = data.csrf_token;

        localStorage.setItem(self.data.csrfKey, token);

        self.callbacks.onLogin(data);
      })
      .fail(function () {
        alert("Invalid username or password.");
      });
  },
  synoLogin: function () {
    SYNOSSO.login();
  },
  events: function () {
    this.data.$synologySsoLogin.on("click", this.synoLogin.bind(this));
    this.data.$loginForm.on("submit", this.login.bind(this));
  },
};

oncallSplash.init();

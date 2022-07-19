from kanpai import Kanpai


class UsersSchemas:

    passwordRegex = r'^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z]).{8,}$'
    passwordError = "Password doesn't meet requirements. At least one digit, one lower and one upper case letter " \
                    "with length at least 8 symbols."

    @staticmethod
    def validateConfirmEmail(requestJson):
        confirmEmailSchema = Kanpai.Object({
            'token': (Kanpai.String(error='Token must be string.')
                      .required(error='Token is required.'))
        })

        return confirmEmailSchema.validate(requestJson)

    @staticmethod
    def validateEmailVerification(requestJson):
        emailVerificationSchema = Kanpai.Object({
            'email': (Kanpai.Email(error="invalid_email_provided")
                      .required(error='please_provide_email')
                      .max(255, error='maximum_allowed_length_is_255'))
        })

        return emailVerificationSchema.validate(requestJson)

    @staticmethod
    def validatePasswordResetRequest(requestJson):
        schema = Kanpai.Object({
            'email': (Kanpai.Email(error="Invalid email provided")
                      .required(error='Please provide email')
                      .max(255, error='Maximum allowed length is 255'))
        })

        return schema.validate(requestJson)

    @staticmethod
    def validatePasswordReset(requestJson):
        schema = Kanpai.Object({
            'token': (Kanpai.String(error="Token should be a string!")
                      .required(error='Please provide token')),

            'password': (Kanpai.String(error='Must be string')
                         .required(error='Please provide user password.')
                         .max(32, error='Maximum allowed length is 32')
                         .match(UsersSchemas.passwordRegex, UsersSchemas.passwordError))
        })

        return schema.validate(requestJson)

    @staticmethod
    def validatePasswordChange(requestJson):
        schema = Kanpai.Object({
            'password': (Kanpai.String(error='Must be string')
                         .required(error='Please provide user password.')
                         .max(32, error='Maximum allowed length is 32')
                         .match(UsersSchemas.passwordRegex, UsersSchemas.passwordError)),
            'newPassword': (Kanpai.String(error='Must be string')
                         .required(error='Please provide user new password.')
                         .max(32, error='Maximum allowed length is 32')
                         .match(UsersSchemas.passwordRegex, UsersSchemas.passwordError))
        })

        return schema.validate(requestJson)



    @staticmethod
    def validatePasswordResetToken(requestJson):
        schema = Kanpai.Object({
            'token': (Kanpai.String(error="Token should be a string!")
                      .required(error='Please provide token')),
        })

        return schema.validate(requestJson)

    @staticmethod
    def editUser(requestJson):
        schema = Kanpai.Object({
            'name': (Kanpai.String(error='Name must be string.')
                     .trim()
                     .required(error='Please provide name.')
                     .max(50, error='Maximum allowed length is 50')
                     .min(2, error='Minimum allowed length is 2')),
            'surname': (Kanpai.String(error='Surname must be string.')
                        .trim()
                        .required(error='Please provide surname.')
                        .max(50, error='Maximum allowed length is 50')
                        .min(2, error='Minimum allowed length is 2')),
            'phone': (Kanpai.String(error='Must be string')
                      .required(error='Please provide phone number')
                      .max(50, error='Maximum allowed length is 50')
                      .min(2, error='Minimum allowed length is 2')),
            'age': (Kanpai.Number().min(1).max(120)
                      .required(error='Please provide age'))
        })

        return schema.validate(requestJson)
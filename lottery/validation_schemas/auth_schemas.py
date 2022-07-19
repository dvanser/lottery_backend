from kanpai import Kanpai


class AuthSchemas:

    @staticmethod
    def validateLogin(requestJson):
        schema = Kanpai.Object({
            'email': (Kanpai.Email(error="Invalid email provided")
                      .required(error='Please provide email.')
                      .max(256, error='Maximum allowed length is 256')),

            'password': (Kanpai.String(error='Must be string')
                         .required(error='Please provide user password.')
                         .max(256, error='Maximum allowed length is 256')
                         .match(r'^.{5,}$', 'Minimum allowed length is 5'))
        })

        return schema.validate(requestJson)

    @staticmethod
    def validateSignup(requestJson):

        signupSchema = Kanpai.Object({
            'email': (Kanpai.Email(error='User email not valid.')
                      .trim()
                      .required(error='Please provide email.')
                      .max(255, error='Maximum allowed length is 255')),
            'password': (Kanpai.String(error='Must be string')
                         .required(error='Please provide user password.')
                         .max(32, error='Maximum allowed length is 32')
                         .match(r'^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z]).{8,}$', 'Password not valid. Password should '
                                                                             'contain at least one lowercase and one '
                                                                             'uppercase letters, one number and '
                                                                             'minimal length is 8 symbols.')),
            'repeatPassword': (Kanpai.String(error='Must be string')
                               .required(error='Please confirm password.')),
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
            'age': (Kanpai.Number(error='Must be integer')
                      .required(error='Please provide age').min(18).max(120))
        })

        return signupSchema.validate(requestJson)

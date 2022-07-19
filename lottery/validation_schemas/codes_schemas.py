from kanpai import Kanpai


class CodesSchemas:

    @staticmethod
    def validateAddCodes(requestJson):
        validateAddCodesSchema = Kanpai.Object({
            'codes': (Kanpai.Array(error='Codes must be an array.')
                      .required(error='Codes is required.'))
        })

        return validateAddCodesSchema.validate(requestJson)
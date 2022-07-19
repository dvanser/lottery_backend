from kanpai import Kanpai


class PrizesSchemas:

    @staticmethod
    def validatePrizesRequestDPD(requestJson):
        confirmEmailSchema = Kanpai.Object({
            'name': (Kanpai.String(error='Must be string')
                       .required(error='Please provide name')
                       .max(255, error='Maximum allowed length is 255')
                       .match(r'^.{1,}$', 'Minimum allowed length is 1')),
            'surname': (Kanpai.String(error='Must be string')
                     .required(error='Please provide surname')
                     .max(255, error='Maximum allowed length is 255')
                     .match(r'^.{1,}$', 'Minimum allowed length is 1')),
            'street': (Kanpai.String(error='Must be string')
                            .required(error='Please provide street')
                            .max(255, error='Maximum allowed length is 255')
                            .match(r'^.{1,}$', 'Minimum allowed length is 1')),
            'city': (Kanpai.String(error='Must be string')
                       .required(error='Please provide street')
                       .max(255, error='Maximum allowed length is 255')
                       .match(r'^.{1,}$', 'Minimum allowed length is 1')),
            'pcode': (Kanpai.String(error='Must be string')
                       .required(error='Please provide postal code')
                       .max(4, error='Maximum allowed length is 4')
                       .match(r'^.{4,}$', 'Minimum allowed length is ')),
            'phone': (Kanpai.String(error='Must be string')
                                   .required(error='Please provide phone')
                                   .max(20, error='Maximum allowed length is 50')
                                   .match(r'^.{8,}$', 'Minimum allowed length is 8')),
            'parcelshopId':(Kanpai.String(error='Must be string')
                                   .required(error='Please provide parcelshop_id')
                                   .max(20, error='Maximum allowed length is 20')
                                   .match(r'^.{1,}$', 'Minimum allowed length is 1')),
            'prizes': (Kanpai.Array(error='Must be array')
                                .required(error='Please provide prizes')),
            'shippingType': (Kanpai.String(error='Must be string')
                       .required(error='Please provide shippingType')
                       .max(255, error='Maximum allowed length is 255')
                       .match(r'^.{1,}$', 'Minimum allowed length is 1'))
        })

        return confirmEmailSchema.validate(requestJson)

    @staticmethod
    def validatePrizesRequestPickUp(requestJson):
        confirmEmailSchema = Kanpai.Object({
            'name': (Kanpai.String(error='Must be string')
                     .required(error='Please provide name')
                     .max(255, error='Maximum allowed length is 255')
                     .match(r'^.{1,}$', 'Minimum allowed length is 1')),
            'surname': (Kanpai.String(error='Must be string')
                        .required(error='Please provide surname')
                        .max(255, error='Maximum allowed length is 255')
                        .match(r'^.{1,}$', 'Minimum allowed length is 1')),
            'phone': (Kanpai.String(error='Must be string')
                      .required(error='Please provide phone')
                      .max(20, error='Maximum allowed length is 50')
                      .match(r'^.{8,}$', 'Minimum allowed length is 8')),
            'prizes': (Kanpai.Array(error='Must be array')
                       .required(error='Please provide prizes')),
            'shippingType': (Kanpai.String(error='Must be string')
                             .required(error='Please provide shippingType')
                             .max(255, error='Maximum allowed length is 255')
                             .match(r'^.{1,}$', 'Minimum allowed length is 1'))
        })

        return confirmEmailSchema.validate(requestJson)

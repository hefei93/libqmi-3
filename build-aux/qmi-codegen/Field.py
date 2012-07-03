#!/usr/bin/env python
# -*- Mode: python; tab-width: 4; indent-tabs-mode: nil -*-
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright (C) 2012 Lanedo GmbH
#

import string

import utils
import VariableFactory
import TypeFactory

"""
The Field class takes care of handling Input and Output TLVs
"""
class Field:

    """
    Constructor
    """
    def __init__(self, prefix, dictionary, common_objects_dictionary):
        # The field prefix, usually the name of the Container,
        #  e.g. "Qmi Message Ctl Something Output"
        self.prefix = prefix
        # The name of the specific field, e.g. "Result"
        self.name = dictionary['name']
        # The specific TLV ID
        self.id = dictionary['id']
        # Whether the field is to be considered mandatory in the message
        self.mandatory = dictionary['mandatory']
        # The type, which must always be "TLV"
        self.type = dictionary['type']

        # Create the composed full name (prefix + name),
        #  e.g. "Qmi Message Ctl Something Output Result"
        self.fullname = dictionary['fullname'] if 'fullname' in dictionary else self.prefix + ' ' + self.name

        # Create our variable object
        self.variable = VariableFactory.create_variable(dictionary, self.fullname)

        # Create the variable name within the Container
        self.variable_name = 'arg_' + string.lower(utils.build_underscore_name(self.name))

        # Create the ID enumeration name
        self.id_enum_name = string.upper(utils.build_underscore_name(self.prefix + ' TLV ' + self.name))

        # Output Fields may have prerequisites
        self.prerequisites = []
        if 'prerequisites' in dictionary:
            self.prerequisites = dictionary['prerequisites']
            # First, look for references to common types
            for prerequisite_dictionary in self.prerequisites:
                if 'common-ref' in prerequisite_dictionary:
                    for common in common_objects_dictionary:
                        if common['type'] == 'prerequisite' and \
                           common['common-ref'] == prerequisite_dictionary['common-ref']:
                           # Replace the reference with a copy of the common dictionary
                           copy = dict(common)
                           self.prerequisites.remove(prerequisite_dictionary)
                           self.prerequisites.append(copy)
                           break
                    else:
                        raise RuntimeError('Common type \'%s\' not found' % prerequisite_dictionary['name'])


    """
    Emit new types required by this field
    """
    def emit_types(self, hfile, cfile):
        if TypeFactory.is_type_emitted(self.fullname) is False:
            TypeFactory.set_type_emitted(self.fullname)
            self.variable.emit_types(hfile)


    """
    Emit the method responsible for getting this TLV from the input/output
    container
    """
    def emit_getter(self, hfile, cfile):
        input_variable_name = utils.build_underscore_name(self.name)
        variable_getter_dec = self.variable.build_getter_declaration('    ', input_variable_name)
        variable_getter_doc = self.variable.build_getter_documentation(' * ', input_variable_name)
        variable_getter_imp = self.variable.build_getter_implementation('    ', 'self->' + self.variable_name, input_variable_name, True)
        translations = { 'name'                : self.name,
                         'variable_name'       : self.variable_name,
                         'variable_getter_dec' : variable_getter_dec,
                         'variable_getter_doc' : variable_getter_doc,
                         'variable_getter_imp' : variable_getter_imp,
                         'underscore'          : utils.build_underscore_name(self.name),
                         'prefix_camelcase'    : utils.build_camelcase_name(self.prefix),
                         'prefix_underscore'   : utils.build_underscore_name(self.prefix) }

        # Emit the getter header
        template = (
            '\n'
            'gboolean ${prefix_underscore}_get_${underscore} (\n'
            '    ${prefix_camelcase} *self,\n'
            '${variable_getter_dec}'
            '    GError **error);\n')
        hfile.write(string.Template(template).substitute(translations))

        # Emit the getter source
        template = (
            '\n'
            '/**\n'
            ' * ${prefix_underscore}_get_${underscore}:\n'
            ' * @self: a ${prefix_camelcase}.\n'
            '${variable_getter_doc}'
            ' * @error: a #GError.\n'
            ' *\n'
            ' * Get the \'${name}\' field from @self.\n'
            ' *\n'
            ' * Returns: #TRUE if the field is found, #FALSE otherwise.\n'
            ' */\n'
            'gboolean\n'
            '${prefix_underscore}_get_${underscore} (\n'
            '    ${prefix_camelcase} *self,\n'
            '${variable_getter_dec}'
            '    GError **error)\n'
            '{\n'
            '    g_return_val_if_fail (self != NULL, FALSE);\n'
            '\n'
            '    if (!self->${variable_name}_set) {\n'
            '        g_set_error (error,\n'
            '                     QMI_CORE_ERROR,\n'
            '                     QMI_CORE_ERROR_TLV_NOT_FOUND,\n'
            '                     "Field \'${name}\' was not found in the message");\n'
            '        return FALSE;\n'
            '    }\n'
            '\n'
            '${variable_getter_imp}'
            '\n'
            '    return TRUE;\n'
            '}\n')
        cfile.write(string.Template(template).substitute(translations))


    """
    Emit the method responsible for setting this TLV in the input/output
    container
    """
    def emit_setter(self, hfile, cfile):
        input_variable_name = utils.build_underscore_name(self.name)
        variable_setter_dec = self.variable.build_setter_declaration('    ', input_variable_name)
        variable_setter_doc = self.variable.build_setter_documentation(' * ', input_variable_name)
        variable_setter_imp = self.variable.build_setter_implementation('    ', input_variable_name, 'self->' + self.variable_name)
        translations = { 'name'                : self.name,
                         'variable_name'       : self.variable_name,
                         'variable_setter_dec' : variable_setter_dec,
                         'variable_setter_doc' : variable_setter_doc,
                         'variable_setter_imp' : variable_setter_imp,
                         'underscore'          : utils.build_underscore_name(self.name),
                         'prefix_camelcase'    : utils.build_camelcase_name(self.prefix),
                         'prefix_underscore'   : utils.build_underscore_name(self.prefix) }

        # Emit the setter header
        template = (
            '\n'
            'gboolean ${prefix_underscore}_set_${underscore} (\n'
            '    ${prefix_camelcase} *self,\n'
            '${variable_setter_dec}'
            '    GError **error);\n')
        hfile.write(string.Template(template).substitute(translations))

        # Emit the setter source
        template = (
            '\n'
            '/**\n'
            ' * ${prefix_underscore}_set_${underscore}:\n'
            ' * @self: a ${prefix_camelcase}.\n'
            '${variable_setter_doc}'
            ' * @error: a #GError.\n'
            ' *\n'
            ' * Set the \'${name}\' field in the message.\n'
            ' *\n'
            ' * Returns: #TRUE if @value was successfully set, #FALSE otherwise.\n'
            ' */\n'
            'gboolean\n'
            '${prefix_underscore}_set_${underscore} (\n'
            '    ${prefix_camelcase} *self,\n'
            '${variable_setter_dec}'
            '    GError **error)\n'
            '{\n'
            '    g_return_val_if_fail (self != NULL, FALSE);\n'
            '\n'
            '    self->${variable_name}_set = TRUE;\n'
            '${variable_setter_imp}'
            '\n'
            '    return TRUE;\n'
            '}\n')
        cfile.write(string.Template(template).substitute(translations))


    """
    Emit the code responsible for adding the TLV to the QMI message
    """
    def emit_input_tlv_add(self, f, line_prefix):
        translations = { 'name'          : self.name,
                         'tlv_id'        : self.id_enum_name,
                         'variable_name' : self.variable_name,
                         'lp'            : line_prefix }

        template = (
            '${lp}guint8 buffer[1024];\n'
            '${lp}guint16 buffer_len = 1024;\n'
            '${lp}guint8 *buffer_aux = buffer;\n'
            '\n')
        f.write(string.Template(template).substitute(translations))

        # Now, write the contents of the variable into the buffer
        self.variable.emit_buffer_write(f, line_prefix, 'input->' + self.variable_name, 'buffer_aux', 'buffer_len')

        template = (
            '\n'
            '${lp}if (!qmi_message_tlv_add (self,\n'
            '${lp}                          (guint8)${tlv_id},\n'
            '${lp}                          (1024 - buffer_len),\n'
            '${lp}                          buffer,\n'
            '${lp}                          error)) {\n'
            '${lp}    g_prefix_error (error, \"Couldn\'t set the ${name} TLV: \");\n'
            '${lp}    qmi_message_unref (self);\n'
            '${lp}    return NULL;\n'
            '${lp}}\n')
        f.write(string.Template(template).substitute(translations))


    """
    Emit the code responsible for checking prerequisites in output TLVs
    """
    def emit_output_prerequisite_check(self, f, line_prefix):
        if self.prerequisites == []:
            f.write('%s/* No Prerequisites for field */\n' % line_prefix)
            return

        for prerequisite in self.prerequisites:
            translations = { 'lp'                     : line_prefix,
                             'prerequisite_field'     : utils.build_underscore_name(prerequisite['field']),
                             'prerequisite_operation' : prerequisite['operation'],
                             'prerequisite_value'     : prerequisite['value'] }
            template = (
                '${lp}/* Prerequisite.... */\n'
                '${lp}if (!(self->arg_${prerequisite_field} ${prerequisite_operation} ${prerequisite_value}))\n'
                '${lp}    break;\n')
            f.write(string.Template(template).substitute(translations))


    """
    Emit the code responsible for retrieving the TLV from the QMI message
    """
    def emit_output_tlv_get(self, f, line_prefix):
        translations = { 'name'                 : self.name,
                         'container_underscore' : utils.build_underscore_name (self.prefix),
                         'tlv_id'               : self.id_enum_name,
                         'variable_name'        : self.variable_name,
                         'lp'                   : line_prefix,
                         'error'                : 'error' if self.mandatory == 'yes' else 'NULL'}

        template = (
            '${lp}guint8 *buffer;\n'
            '${lp}guint16 buffer_len;\n'
            '\n'
            '${lp}if (qmi_message_tlv_get (message,\n'
            '${lp}                         ${tlv_id},\n'
            '${lp}                         &buffer_len,\n'
            '${lp}                         &buffer,\n'
            '${lp}                         ${error})) {\n'
            '${lp}    self->${variable_name}_set = TRUE;\n'
            '\n')
        f.write(string.Template(template).substitute(translations))

        # Now, read the contents of the buffer into the variable
        self.variable.emit_buffer_read(f, line_prefix + '    ', 'self->' + self.variable_name, 'buffer', 'buffer_len')

        template = (
            '\n'
            '${lp}    /* The remaining size of the buffer needs to be 0 if we successfully read the TLV */\n'
            '${lp}    if (buffer_len > 0) {\n'
            '${lp}        g_warning ("Left \'%u\' bytes unread when getting the \'${name}\' TLV", buffer_len);\n'
            '${lp}    }\n')

        if self.mandatory == 'yes':
            template += (
                '${lp}} else {\n'
                '${lp}    g_prefix_error (error, \"Couldn\'t get the ${name} TLV: \");\n'
                '${lp}    ${container_underscore}_unref (self);\n'
                '${lp}    return NULL;\n'
                '${lp}}\n')
        else:
            template += (
                '${lp}}\n')
        f.write(string.Template(template).substitute(translations))


    """
    Emit the method responsible for creating a printable representation of the TLV
    """
    def emit_output_tlv_get_printable(self, f):
        if TypeFactory.is_get_printable_emitted(self.fullname):
            return

        TypeFactory.set_get_printable_emitted(self.fullname)

        translations = { 'name'       : self.name,
                         'tlv_id'     : self.id_enum_name,
                         'underscore' : utils.build_underscore_name (self.fullname) }
        template = (
            '\n'
            'static gchar *\n'
            '${underscore}_get_printable (\n'
            '    QmiMessage *message,\n'
            '    const gchar *line_prefix)\n'
            '{\n'
            '    guint8 *buffer;\n'
            '    guint16 buffer_len;\n'
            '\n'
            '    if (qmi_message_tlv_get (message,\n'
            '                             ${tlv_id},\n'
            '                             &buffer_len,\n'
            '                             &buffer,\n'
            '                             NULL)) {\n'
            '        GString *printable;\n'
            '\n'
            '        printable = g_string_new ("");\n')
        f.write(string.Template(template).substitute(translations))

        # Now, read the contents of the buffer into the printable representation
        self.variable.emit_get_printable(f, '        ', 'printable', 'buffer', 'buffer_len')

        template = (
            '\n'
            '        /* The remaining size of the buffer needs to be 0 if we successfully read the TLV */\n'
            '        if (buffer_len > 0) {\n'
            '            g_warning ("Left \'%u\' bytes unread when getting the \'${name}\' TLV as printable", buffer_len);\n'
            '        }\n'
            '\n'
            '        return g_string_free (printable, FALSE);\n'
            '    }\n'
            '\n'
            '    return NULL;\n'
            '}\n')
        f.write(string.Template(template).substitute(translations))

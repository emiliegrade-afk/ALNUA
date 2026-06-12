-- Add 'compute' as a valid BOM category (Pi, SBC, main boards)

ALTER TABLE public.bom_eve
  DROP CONSTRAINT IF EXISTS bom_eve_category_check;

ALTER TABLE public.bom_eve
  ADD CONSTRAINT bom_eve_category_check
  CHECK (category IN (
    'vision', 'audio', 'moteur', 'alimentation',
    'microcontroleur', 'chassis', 'compute', 'autre'
  ));
